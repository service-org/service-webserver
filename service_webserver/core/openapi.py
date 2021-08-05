#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import inspect
import typing as t

from logging import getLogger
from functools import partial
from inspect import Parameter
from inspect import Signature
from pydantic import BaseModel
from pydantic import BaseConfig
from pydantic import create_model
from dataclasses import is_dataclass
from pydantic.fields import Required
from pydantic.fields import SHAPE_SET
from pydantic.fields import FieldInfo
from pydantic.fields import Undefined
from pydantic.fields import ModelField
from pydantic.schema import ForwardRef
from pydantic.fields import SHAPE_LIST
from pydantic.fields import SHAPE_TUPLE
from pydantic.fields import BoolUndefined
from pydantic.fields import SHAPE_SEQUENCE
from pydantic.fields import SHAPE_SINGLETON
from pydantic.typing import NoArgAnyCallable
from service_core.core.service import Service
from pydantic.class_validators import Validator
from pydantic.typing import evaluate_forwardref
from pydantic.fields import SHAPE_TUPLE_ELLIPSIS
from pydantic.schema import get_annotation_from_field_info

from .request import Request
from .response import Response
from .inspection import params
from .inspection.depent import Dependent
from .inspection.checking import is_subclass
from .inspection.security.oauth2 import OAuth2
from .inspection.security.base import SecurityBase
from .inspection.security.base import SecurityScheme
from .inspection.security.oauth2 import SecurityScopes
from .inspection.security.openid_connect import OpenIdConnect

logger = getLogger(__name__)
sequence_types = (
    list, set, tuple
)
sequence_shapes = {
    SHAPE_SET, SHAPE_LIST,
    SHAPE_TUPLE, SHAPE_SEQUENCE,
    SHAPE_TUPLE_ELLIPSIS
}
sequence_shapes_mapping = {
    SHAPE_SET: set, SHAPE_LIST: list,
    SHAPE_TUPLE: tuple, SHAPE_SEQUENCE: list,
    SHAPE_TUPLE_ELLIPSIS: list
}
CacheKey = t.Tuple[t.Optional[t.Callable[..., t.Any]], t.Tuple[t.Text, ...]]


def gen_operation_id_for_path(*, name: t.Text, path: t.Text, method: t.Text) -> t.Text:
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
    return operation_id + '_' + method.lower()


def add_param_model_field_to_dependent(*, field: ModelField, dependent: Dependent) -> None:
    """ 字段注入到依赖树

    @param field: 字段模型
    @param dependent: 依赖对象
    @return: None
    """
    field_info = t.cast(params.Param, field.field_info)
    # 当字段模型的field_info为path时将其记录到依赖树的path_fields
    if field_info.in_ == params.ParamTypes.path:
        dependent.path_fields.append(field)
    # 当字段模型的field_info为query时将其记录到依赖树的query_fields
    if field_info.in_ == params.ParamTypes.query:
        dependent.query_fields.append(field)
    # 当字段模型的field_info为header时将其记录到依赖树的header_fields
    if field_info.in_ == params.ParamTypes.header:
        dependent.header_fields.append(field)
    # 当字段模型的field_info为cookie时将其记录到依赖树的cookies_fields
    if field_info.in_ == params.ParamTypes.cookie:
        dependent.cookie_fields.append(field)


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


def is_scalar_field(field: ModelField) -> bool:
    """ 是否为标准字段

    @param field: 模型字段
    @return: bool
    """
    field_info = field.field_info
    if not (
            # 字段必须是单值类型
            field.shape == SHAPE_SINGLETON
            # 注解不是模型类子类
            and not is_subclass(field.type_, BaseModel)
            # 注解不是序列类子类
            and not is_subclass(field.type_, sequence_types + (dict,))
            # field_info不是body
            and not isinstance(field_info, params.Body)
    ):
        return False
    if not field.sub_fields:
        return True
    for sub_field in field.sub_fields:
        if is_scalar_field(sub_field):
            continue
        return False
    return True


def is_scalar_sequence_field(field: ModelField) -> bool:
    """ 是否为标准序列字段

    @param field: 模型字段
    @return: bool
    """
    if (field.shape in sequence_shapes) and not is_subclass(field.type_, BaseModel):
        if not field.sub_fields:
            return True
        for sub_field in field.sub_fields:
            if is_scalar_field(sub_field):
                continue
            return False
    if is_subclass(field.type_, sequence_types):
        return True
    return False


def gen_param_field(
        *,
        param: Parameter,
        param_name: t.Text,
        param_type: t.Optional[params.ParamTypes] = None,
        ignore_default_val: t.Optional[bool] = None,
        default_field_info: t.Optional[t.Type[params.Param]] = None,
) -> ModelField:
    """ 生成请求模型字段

    @param param: 参数对象
    @param param_name: 参数名称
    @param param_type: 参数类型
    @param ignore_default_val: 忽略参数
    @param default_field_info: 额外数据
    @return: ModelField
    """
    default_value, has_schema = Required, False
    if param.default != param.empty and not ignore_default_val:
        default_value = param.default
    default_field_info = default_field_info or params.Param
    # 如果默认值是FieldInfo的子类实例例如params.X
    if isinstance(default_value, FieldInfo):
        has_schema = True
        field_info = default_value
        default_value = field_info.default
        was_params = isinstance(field_info, params.Param)
        has_inattr = getattr(field_info, 'in_', None) is None
        was_others = was_params and has_inattr
        was_others and setattr(field_info, 'in_', default_field_info.in_)
        param_type and setattr(field_info, 'in_', param_type)
    else:
        field_info = default_field_info(default_value)
    required = default_value == Required
    annotation = param.annotation if param.annotation != param.empty else t.Any
    annotation = get_annotation_from_field_info(annotation, field_info, param_name)
    if not field_info.alias and getattr(field_info, 'convert_underscores', None):
        alias = param.name.replace('_', '-')
    else:
        alias = field_info.alias or param.name
    default = None if required else default_value
    model_field = gen_model_field(
        name=param.name, type_=annotation, default=default, alias=alias, required=required,
        field_info=field_info
    )
    model_field.required = required
    as_body = not has_schema and not is_scalar_field(field=model_field)
    model_field.field_info = params.Body(field_info.default) if as_body else model_field.field_info
    return model_field


def get_annotation_object(param: Parameter, global_ns: t.Dict[t.Text, t.Any]) -> t.Any:
    """ 从注解获取原始对应的对象

    @param param: 参数对象
    @param global_ns: 命名空间

    @return: t.Any
    """
    annotation = param.annotation
    annotation = ForwardRef(annotation) if isinstance(annotation, t.Text) else annotation
    # 通过对象的全局命名空间反射获取其注解的原始对象
    to_object = partial(evaluate_forwardref, globalns=global_ns, localns=global_ns)
    return to_object(annotation) if isinstance(annotation, ForwardRef) else annotation


def get_sub_dependent_from_call(
        *,
        depended: params.Depended,
        call: t.Callable[..., t.Any],
        path: t.Text,
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
) -> Dependent:
    """ 从调用对象获取子依赖树

    @param depended: 参数默认值
    @param call: 调用对象
    @param path: 请求路径
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @return: Dependent
    """
    security_scheme = None
    security_scopes = security_scopes or []
    # 当参数默认值为Security对象则收集它的安全范围
    if isinstance(depended, params.Security):
        security_scopes.extend(depended.scopes)
    # 当默认值的dependent是SecurityBase子类实例
    if isinstance(call, SecurityBase):
        auths = (OAuth2, OpenIdConnect)
        # 除了OAuth2和OpenIdConnect认证需要scopes其它的不需要
        scopes = security_scopes if isinstance(call, auths) else []
        # 构建一个新的SecurityScheme,不要尝试去直接赋值security_scopes
        security_scheme = SecurityScheme(scheme=call, scopes=scopes)
    # 递归构建依赖树并自动挂载到上级依赖对象的sub_dependents上
    sub_dependent = get_dependent_from_call(
        path=path, call=call, name=name, use_cache=depended.use_cache,
        security_scopes=security_scopes
    )
    sub_dependent.security_scopes = security_scopes
    # 记录上面构建的SecurityScheme,此时的call其实是继承自SecurityBase的认证实例
    security_scheme and sub_dependent.security_schemes.append(security_scheme)
    return sub_dependent


def get_sub_dependent_from_param(
        *,
        param: Parameter,
        path: t.Text,
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
) -> Dependent:
    """ 从调用对象参数获取子依赖树

    @param param: 参数对象
    @param path: 请求路径
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @return: Dependent
    """
    # 获取参数的默认值
    depended = param.default
    # 如果depends对象存在dependent则将其作为call否则将反射后的注解作为call递归解析依赖树
    call = depended.dependent if depended.dependent else param.annotation
    name = name or param.name
    return get_sub_dependent_from_call(
        depended=depended,
        call=call,
        path=path,
        name=name,
        security_scopes=security_scopes
    )


def get_flat_dependent(
        dependent: Dependent,
        *,
        skip_repeats: t.Optional[bool] = None,
        visited: t.Optional[t.List[CacheKey]] = None
) -> Dependent:
    """ 生成扁平的依赖树

    @param dependent: 依赖对象
    @param skip_repeats: 跳过重复?
    @param visited: 访问历史
    @return: Dependent
    """
    # 存储已注入的依赖对象的缓存键
    visited = visited or []
    visited.append(dependent.cache_key)
    # 创建一个顶层依赖树对象供注入
    flat_dependent = Dependent(
        path=dependent.path,
        use_cache=dependent.use_cache,
        path_fields=dependent.path_fields.copy(),
        query_fields=dependent.query_fields.copy(),
        header_fields=dependent.header_fields.copy(),
        cookie_fields=dependent.cookie_fields.copy(),
        body_fields=dependent.cookie_fields.copy(),
        security_schemes=dependent.security_schemes.copy()
    )
    for sub_dependent in dependent.sub_dependents:
        # 跳过已注入到flat_dependent的依赖对象
        if skip_repeats and sub_dependent.cache_key in visited:
            continue
        # 递归的创建依赖树并收集参数
        sub_flat_dependent = get_flat_dependent(
            sub_dependent, skip_repeats=skip_repeats, visited=visited
        )
        # 将收集到的参数由下向上传递
        flat_dependent.body_fields.extend(sub_flat_dependent.body_fields)
        flat_dependent.path_fields.extend(sub_flat_dependent.path_fields)
        flat_dependent.query_fields.extend(sub_flat_dependent.query_fields)
        flat_dependent.header_fields.extend(sub_flat_dependent.header_fields)
        flat_dependent.cookie_fields.extend(sub_flat_dependent.cookie_fields)
        flat_dependent.security_schemes.extend(sub_flat_dependent.security_schemes)
    return flat_dependent


def add_non_param_to_dependent(*, param: Parameter, dependent: Dependent) -> t.Optional[bool]:
    """ 忽略掉不作为字段的参数

    @param param: 参数对象
    @param dependent: 依赖对象
    @return: t.Optional[bool]
    """
    # 忽略掉SecurityScopes并记录其字段名
    if is_subclass(param.annotation, SecurityScopes):
        dependent.security_scopes_field_name = param.name
        return True
    # 忽略掉Service子类字段并记录其字段名
    if is_subclass(param.annotation, Service):
        dependent.service_field_name = param.name
        return True
    # 忽略掉Request子类字段并记录其字段名
    if is_subclass(param.annotation, Request):
        dependent.request_field_name = param.name
        return True
    # 忽略掉Response子类字段并记录其字段名
    if is_subclass(param.annotation, Response):
        dependent.response_field_name = param.name
        return True
    return None


def get_body_field(*, dependent: Dependent, name: t.Text) -> t.Optional[ModelField]:
    """ 获取body字段

    @param dependent: 依赖对象
    @param name: 字段名称
    @return: t.Optional[ModelField]
    """
    # 获取扁平的依赖树对象,其实就是递归的把参数对象由下而上收集起来
    flat_dependent = get_flat_dependent(dependent, skip_repeats=True)
    if not flat_dependent.body_fields:
        return
    body_model_name, body_field_media_types = f'Body_{name}', []
    BodyModel = create_model(body_model_name)
    BodyFieldInfo, required = params.Body, False
    for field in flat_dependent.body_fields:
        field.field_info.embed = True
        # 收集的所有body字段加入模型对象中
        BaseModel.__fields__[field.name] = field
        # 有一个参数是必填则认为body必须的
        required = required if required else field.required
        # 如果字段的默认值是文件则构造file
        is_file_field = isinstance(field.field_info, params.File)
        BodyFieldInfo = params.File if is_file_field else BodyFieldInfo
        # 如果字段的默认值是form则构建form
        is_form_field = isinstance(field.field_info, params.Form)
        BodyFieldInfo = params.Form if is_form_field else BodyFieldInfo
        # 当不是上面值则归为body并记录类型
        BodyFieldInfo == params.Body and body_field_media_types.append(
            field.field_info.media_type
        )
    body_field_info_data = {'default': None}
    # 如果只有一个body类型参数则将其类型设置为默认或用户传递的类型
    if BodyFieldInfo == params.Body and len(body_field_media_types) == 1:
        body_field_info_data['media_type'] = body_field_media_types[0]
    # 根据上面的BodyModel,BodyFieldInfo来构造body field字段
    body_field = gen_model_field(
        name='body', type_=BodyModel, required=required, alias='body',
        field_info=BodyFieldInfo(**body_field_info_data)
    )
    return body_field


def gen_signature_of_call(call: t.Callable[..., t.Any]) -> Signature:
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


def get_field_names_from_path(path: t.Text) -> t.Set[t.Text]:
    """ 从请求路径获取名称列表

    用途: 主要用于后面判断是否为路径参数

    @param path: 请求路径, 如: /items/{item_id}/?
    @return: t.Set[t.Text]
    """
    return set(re.findall(r'{(.*?)}', path))


def get_dependent_from_call(
        *,
        path: t.Text,
        call: t.Callable[..., t.Any],
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
        use_cache: bool = True
) -> Dependent:
    """ 从调用对象获取依赖树

    @param path: 请求路径, 如: /items/{item_id}/?
    @param call: 调用对象
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @param use_cache: 是否使用缓存?
    @return: Dependent
    """
    # 获取路径参数中的参数名集合,用于判断是否为路径参数
    path_field_names = get_field_names_from_path(path)
    # 重新为调用对象生成签名对象,用于反射所有参数的注解
    call_signature = gen_signature_of_call(call)
    # 创建一个当前依赖对象
    dependent = Dependent(name=name, path=path, call=call, use_cache=use_cache)
    for param_name, param in call_signature.parameters.items():
        # 当参数值为依赖对象时,递归解析其dependent并将其注入到当前依赖树
        if isinstance(param.default, params.Depended):
            sub_dependent = get_sub_dependent_from_param(param=param,
                                                         path=path,
                                                         security_scopes=security_scopes)
            dependent.sub_dependents.append(sub_dependent)
            continue
        # 当参数注解为特定类例如Request,Response,Service,Scope时忽略
        if add_non_param_to_dependent(param=param, dependent=dependent):
            continue
        param_model_field = gen_param_field(
            param=param, default_field_info=params.Query, param_name=param_name
        )
        # 当参数名称存在于路径参数名集合中时,表示此字段为路径参数
        if param_name in path_field_names:
            right_type = is_scalar_field(param_model_field)
            right_type or logger.error(f'path params must one of supported types')
            ignore_default_val = not isinstance(param.default, params.Path)
            param_model_field = gen_param_field(
                param=param, default_field_info=params.Path, param_type=params.ParamTypes.path,
                param_name=param_name, ignore_default_val=ignore_default_val
            )
            add_param_model_field_to_dependent(field=param_model_field, dependent=dependent)
        # 当参数为除了路径参数之外的其他标准参数则将其作为查询参数
        elif is_scalar_field(field=param_model_field):
            add_param_model_field_to_dependent(field=param_model_field, dependent=dependent)
        # 当参数注解类型为序列类且默认值为Query或Header实例时候
        elif isinstance(param.default, (params.Query, params.Header)
                        ) and is_scalar_sequence_field(param_model_field):
            add_param_model_field_to_dependent(field=param_model_field, dependent=dependent)
        else:
            as_body = isinstance(param_model_field.field_info, params.Body)
            as_body or logger.error(f'param {param_model_field.name} can only be request body')
            dependent.body_fields.append(param_model_field)
    return dependent
