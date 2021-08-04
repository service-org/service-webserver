#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import inspect
import typing as t

from functools import partial
from inspect import Parameter
from inspect import Signature
from pydantic import BaseConfig
from pydantic.fields import FieldInfo
from pydantic.fields import Undefined
from pydantic.fields import ModelField
from pydantic.schema import ForwardRef
from pydantic.fields import BoolUndefined
from pydantic.typing import NoArgAnyCallable
from service_core.core.service import Service
from pydantic.class_validators import Validator
from pydantic.typing import evaluate_forwardref

from .request import Request
from .response import Response
from .inspection import params
from .inspection.depent import Dependant
from .inspection.checking import is_subclass
from .inspection.security.oauth2 import OAuth2
from .inspection.security.base import SecurityBase
from .inspection.security.base import SecurityScheme
from .inspection.security.openid_connect import OpenIdConnect


def gen_operation_id_for_path(
        *,
        name: t.Text,
        path: t.Text,
        method: t.Text
) -> t.Text:
    """ 生成路径操作标识

    doc: https://swagger.io/specification/#operation-object

    @param name: 路由名称
    @param path: 请求路径
    @param method: 请求方法
    @return: t.Text
    """
    operation_id = name + path
    # path规范必须以/开头,所以/会被自动转换为-
    operation_id = re.sub(r'[^0-9a-zA-Z_]', '_', operation_id)
    operation_id = operation_id + '_' + method.lower()
    return operation_id


def gen_model_field(
        *,
        name: t.Text,
        type_: t.Type[t.Any],
        class_validators: t.Optional[t.Dict[t.Text, Validator]] = None,
        model_config: t.Type[BaseConfig] = None,
        default: t.Any = None,
        default_factory: t.Optional[NoArgAnyCallable] = None,
        required: BoolUndefined = Undefined,
        alias: str = None,
        field_info: t.Optional[FieldInfo] = None,
) -> ModelField:
    """ 生成响应模型字段

    @param name: 字段名称
    @param type_: 验证模型
    @param class_validators: 加验证器
    @param model_config: 模型配置
    @param default: 默认值
    @param default_factory: 默认值函数
    @param required: 必要字段?
    @param alias: 字段别名
    @param field_info: 额外信息辅助验证
    @return: ModelField
    """
    model_config = model_config or BaseConfig
    field_info = field_info or FieldInfo(None)
    class_validators = class_validators or {}

    # 模型字段,用其记录字段的type_和model_config和field_info
    return ModelField(
        name=name,
        type_=type_,
        class_validators=class_validators,
        model_config=model_config,
        default=default,
        default_factory=default_factory,
        required=required,
        alias=alias,
        field_info=field_info
    )


def get_annotation_object(
        param: Parameter,
        global_ns: t.Dict[t.Text, t.Any]
) -> t.Any:
    """ 从注解获取原始对应的对象

    @param param: 参数对象
    @param global_ns: 命名空间
    @return: t.Any
    """
    annotation = param.annotation
    if isinstance(annotation, t.Text):
        annotation = ForwardRef(annotation)
    # 通过对象的全局命名空间反射获取其注解的原始对象
    to_object = partial(evaluate_forwardref,
                        globalns=global_ns,
                        localns=global_ns)
    if isinstance(annotation, ForwardRef):
        annotation = to_object(annotation)
    return annotation


def add_non_param_to_dependency(
        *,
        param: Parameter,
        dependant: Dependant,
) -> t.Optional[bool]:
    """ 忽略掉不作为字段的参数

    @param param: 参数对象
    @param dependant: 依赖对象
    @return: t.Optional[bool]
    """
    if is_subclass(param.annotation, Request):
        dependant.request_field_name = param.name
        return True
    if is_subclass(param.annotation, Response):
        dependant.response_field_name = param.name
        return True
    if is_subclass(param.annotation, BaseService):

    return None


def get_sub_dependant_from_call(
        *,
        depends: params.Depends,
        call: t.Callable[..., t.Any],
        path: t.Text,
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
) -> Dependant:
    """ 从调用对象获取子依赖树

    @param depends: 参数默认值
    @param call: 调用对象
    @param path: 请求路径
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @return: Dependant
    """
    security_scheme = None
    security_scopes = security_scopes or []
    # 当参数默认值为Security对象则收集它的安全范围
    if isinstance(depends, params.Security):
        security_scopes.extend(depends.scopes)
    # 当默认值的dependency是SecurityBase子类实例
    if isinstance(call, SecurityBase):
        authes = (OAuth2, OpenIdConnect)
        # 除了OAuth2和OpenIdConnect认证需要scopes其它的不需要
        scopes = security_scopes if isinstance(call, authes) else []
        # 构建一个新的SecurityScheme,不要尝试去直接赋值security_scopes
        security_scheme = SecurityScheme(scheme=call, scopes=scopes)
    # 递归构建依赖树并自动挂载到上级依赖对象的dependencies上
    sub_dependant = get_dependant_from_call(path=path,
                                            call=call,
                                            name=name,
                                            use_cache=depends.use_cache,
                                            security_scopes=security_scopes)
    sub_dependant.security_scopes = security_scopes
    # 记录上面构建的SecurityScheme,此时的call其实是继承自SecurityBase的认证实例
    security_scheme and sub_dependant.security_schemes.append(security_scheme)
    return sub_dependant


def get_sub_dependant_from_param(
        *,
        param: Parameter,
        path: t.Text,
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
) -> Dependant:
    """ 从调用对象参数获取子依赖树

    @param param: 参数对象
    @param path: 请求路径
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @return: Dependant
    """
    # 获取参数的默认值
    depends = param.default
    # 如果depends对象存在dependency则将其作为call否则将反射后的注解作为call递归解析依赖树
    call = depends.dependency if depends.dependency else param.annotation
    return get_sub_dependant_from_call(
        depends=depends,
        call=call,
        path=path,
        name=name,
        security_scopes=security_scopes
    )


def gen_signature_of_call(
        call: t.Callable[..., t.Any]
) -> Signature:
    """ 从调用对象生成其签名对象

    @param call: 调用对象
    @return: Signature
    """
    # 解析调用对象的签名信息
    signature = inspect.signature(call)
    # 获取调用对象的全局字典
    global_ns = getattr(call, '__globals__', {})
    # 将参数的注解反射为对象
    to_object = partial(get_annotation_object, global_ns=global_ns)
    # 重新构建调用对象的签名
    parameters = [Parameter(name=p.name,
                            kind=p.kind,
                            default=p.default,
                            annotation=to_object(p.annotation)
                            ) for p in signature.parameters.values()]
    return Signature(parameters=parameters)


def get_field_names_from_path(
        path: t.Text
) -> t.Set[t.Text]:
    """ 从请求路径获取名称列表

    用途: 主要用于后面判断是否为路径参数

    @param path: 请求路径, 如: /items/{item_id}/?
    @return: t.Set[t.Text]
    """
    return set(re.findall(r'{(.*?)}', path))


def get_dependant_from_call(
        *,
        path: t.Text,
        call: t.Callable[..., t.Any],
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
        use_cache: bool = True
) -> Dependant:
    """ 从调用对象获取依赖树

    @param path: 请求路径, 如: /items/{item_id}/?
    @param call: 调用对象
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @param use_cache: 是否使用缓存?
    @return: Dependant
    """
    # 获取路径参数中的参数名集合,用于判断是否为路径参数
    path_field_names = get_field_names_from_path(path)
    # 重新为调用对象生成签名对象,主要反射所有参数的注解
    call_signature = gen_signature_of_call(call)
    call_parameters = call_signature.parameters
    # 创建一个当前依赖对象
    dependant = Dependant(name=name, path=path, call=call, use_cache=use_cache)
    # 遍历当前调用对象参数
    for param_name, param in call_parameters.items():
        # 当参数同样为为依赖对象时,递归解析其dependency调用对象并将其注入到当前依赖对象
        if isinstance(param.default, params.Depends):
            sub_dependant = get_sub_dependant_from_param(param=param,
                                                         path=path,
                                                         name=param_name,
                                                         security_scopes=security_scopes)
            dependant.dependencies.append(sub_dependant)
            continue
    return dependant
