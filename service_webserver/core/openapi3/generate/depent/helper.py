#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com
from __future__ import annotations

import re
import typing as t

from inspect import _empty
from inspect import Parameter
from logging import getLogger
from pydantic import BaseModel
from pydantic import create_model
from pydantic.fields import Required
from pydantic.fields import FieldInfo
from pydantic.fields import ModelField
from service_core.core.service import Service
from service_webserver.core.request import Request
from service_webserver.core.response import Response
from pydantic.schema import get_annotation_from_field_info
from service_webserver.core.openapi3.security.base import BaseSecurity
from service_webserver.core.openapi3.security.scopes import SecurityScopes
from service_webserver.core.openapi3.security.scheme import SecurityScheme
from service_webserver.core.openapi3.security.builtins.oauth2 import OAuth2
from service_webserver.core.openapi3.security.builtins.openid_connect import OpenIdConnect

from . import params
from .models import Dependent
from .checks import is_subclass
from .field import gen_model_field
from .checks import is_scalar_field
from .typed import get_typed_signature
from .checks import is_scalar_sequence_field

logger = getLogger(__name__)
DependantIdent = t.Tuple[t.Callable[..., t.Any], t.Tuple[t.Text, ...]]


def get_flat_dependent(
        dependent: Dependent,
        *, skip_repeats: t.Optional[bool] = None,
        storage: t.Optional[t.List[DependantIdent]] = None
) -> Dependent:
    """ 生成扁平的依赖树
    @param dependent: 依赖对象
    @param skip_repeats: 跳过重复?
    @param storage: 零时存储器
    @return: Dependent
    """
    # 存储已注入的依赖对象的唯一键
    storage = storage or []
    storage.append(dependent.ident)
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
        if skip_repeats and sub_dependent.ident in storage:
            continue
        sub_flat_dependent = get_flat_dependent(
            sub_dependent, skip_repeats=skip_repeats, storage=storage
        )
        # 将收集到的字段由下向上传递到顶层依赖树使其扁平化的存储所有字段
        flat_dependent.body_fields.extend(sub_flat_dependent.body_fields)
        flat_dependent.path_fields.extend(sub_flat_dependent.path_fields)
        flat_dependent.query_fields.extend(sub_flat_dependent.query_fields)
        flat_dependent.header_fields.extend(sub_flat_dependent.header_fields)
        flat_dependent.cookie_fields.extend(sub_flat_dependent.cookie_fields)
        flat_dependent.security_schemes.extend(sub_flat_dependent.security_schemes)
    return flat_dependent


def get_body_field(*, dependent: Dependent, name: t.Text) -> t.Optional[ModelField]:
    """ 获取body字段
    @param dependent: 依赖对象
    @param name: 字段名称
    @return: t.Optional[ModelField]
    """
    flat_dependent = get_flat_dependent(dependent, skip_repeats=True)
    if not flat_dependent.body_fields:
        return
    body_model_name, body_field_media_types = f'Body_{name}', []
    BodyModel = create_model(body_model_name)
    BodyFieldInfo, required = params.Body, False
    for field in flat_dependent.body_fields:
        field.field_info.embed = True
        # 收集的所有body字段加入模型对象中
        BodyModel.__fields__[field.name] = field
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


def add_param_field(*, model_field: ModelField, dependent: Dependent) -> None:
    """ 将字段注入到依赖树

    @param model_field: 模型字段
    @param dependent: 依赖对象
    @return: None
    """
    field_info = t.cast(params.Param, model_field.field_info)
    if field_info.in_ == params.ParamTypes.path:
        dependent.path_fields.append(model_field)
    if field_info.in_ == params.ParamTypes.query:
        dependent.query_fields.append(model_field)
    if field_info.in_ == params.ParamTypes.header:
        dependent.header_fields.append(model_field)
    if field_info.in_ == params.ParamTypes.cookie:
        dependent.cookie_fields.append(model_field)


def gen_param_field(
        *,
        param: Parameter,
        param_name: t.Text,
        ignore_default: t.Optional[bool] = None,
        param_type: t.Optional[params.ParamTypes] = None,
        default_field_info_class: t.Optional[t.Type[params.Param]] = None,
) -> ModelField:
    """ 生成响应用的模型字段

    @param param: 参数对象
    @param param_name: 参数名称
    @param param_type: 参数类型
    @param ignore_default: 忽略掉默认值?
    @param default_field_info_class: 字段类
    @return: ModelField
    """
    default_value, has_schema = Required, False
    # 字段存在默认值且不忽略默认值就设置当前默认值
    default_value = param.default if param.default != param.empty and not ignore_default else default_value
    default_field_info_class = default_field_info_class or params.Param
    # 如果默认值是FieldInfo的子类实例例如params.X
    if isinstance(default_value, FieldInfo):
        has_schema = True
        field_info = default_value
        default_value = field_info.default
        was_params = isinstance(field_info, params.Param)
        has_inattr = getattr(field_info, 'in_', None) is None
        # 判断是否为Body, Form, File等类型字段实例
        was_others = was_params and has_inattr
        # 如果默认的field_info设置则使用它来区分参数
        was_others and setattr(field_info, 'in_', default_field_info_class.in_)
        # 如果设置了param_type则使用它的值来区分参数
        param_type and setattr(field_info, 'in_', param_type)
    else:
        # 如果不是FieldInfo实例则将其归为默认字段参数
        field_info = default_field_info_class(default_value)
    annotation = param.annotation if param.annotation != param.empty else t.Any
    annotation = get_annotation_from_field_info(annotation, field_info, param_name)
    # params.Header参数中定义了参数名是否需要转下划线
    need_convert_underscores = getattr(field_info, 'convert_underscores', None)
    if not field_info.alias and need_convert_underscores:
        alias = param.name.replace('_', '-')
    else:
        alias = field_info.alias or param.name
    required = default_value == Required
    default = None if required else default_value
    model_field = gen_model_field(name=param.name, type_=annotation, default=default,
                                  alias=alias, required=required, field_info=field_info)
    model_field.required = required
    i = not has_schema and not is_scalar_field(model_field)
    model_field.field_info = params.Body(field_info.default) if i else model_field.field_info
    return model_field


def add_non_field_param(*, param: Parameter, dependent: Dependent) -> t.Optional[bool]:
    """ 忽略掉特定注解的字段

    @param param: 参数对象
    @param dependent: 依赖对象
    @return: t.Optional[bool]
    """
    # security_scopes: SecurityScopes
    if is_subclass(param.annotation, SecurityScopes):
        dependent.security_scopes_field_name = param.name
        return True
    # 大型应用中Service被注入到函数首个参数
    if param.annotation is _empty and param.name == 'self':
        return True
    # self: Service
    if is_subclass(param.annotation, Service):
        dependent.service_field_name = param.name
        return True
    # request: Request
    if is_subclass(param.annotation, Request):
        dependent.request_field_name = param.name
        return True
    # response: Response
    if is_subclass(param.annotation, Response):
        dependent.response_field_name = param.name
        return True
    return False


def get_sub_dependent(
        *,
        depended: params.Depended,
        call: t.Callable[..., t.Any],
        path: t.Text,
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
) -> Dependent:
    """ 从调用对象获取子依赖树

    @param depended: 依赖对象
    @param call: 调用对象
    @param path: 请求路径
    @param name: 依赖名称
    @param security_scopes: 安全范围列表
    @return: Dependent
    """
    security_scheme = None
    security_scopes = security_scopes or []
    # current_user: User = Security(get_current_user, scopes=['me'])
    if isinstance(depended, params.Security):
        security_scopes.extend(depended.scopes)
    # oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token url', scopes={'me': ''})
    # token: str = Depended(oauth2_scheme)
    if isinstance(call, BaseSecurity):
        need_scheme_auths = (OAuth2, OpenIdConnect)
        scopes = security_scopes if isinstance(call, need_scheme_auths) else []
        security_scheme = SecurityScheme(scheme=call, scopes=scopes)
    sub_dependent = get_dependent(
        path=path, call=call, name=name,
        use_cache=depended.use_cache,
        security_scopes=security_scopes
    )
    sub_dependent.security_scopes = security_scopes
    security_scheme and sub_dependent.security_schemes.append(security_scheme)
    return sub_dependent


def get_param_sub_dependant(
        *,
        param: Parameter,
        path: t.Text,
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
) -> Dependent:
    """ 从调用对象获取依赖树

    @param param: 参数对象
    @param path: 请求路径
    @param name: 依赖名称
    @param security_scopes: 权限范围列表
    @return: Dependent
    """
    # 参数的默认值此时为依赖对象
    depended = param.default
    # 依赖处理器为空尝试解析注解
    call = depended.dependent if depended.dependent else param.annotation
    name = name or param.name
    return get_sub_dependent(
        depended=depended,
        security_scopes=security_scopes,
        call=call,
        path=path,
        name=name
    )


def get_path_param_names(path: t.Text) -> t.Set[t.Text]:
    """ 从路径获取名称列表

    @param path: 请求路径, 如: /items/{item_id}/?
    @return: t.Set[t.Text]
    """
    return set(re.findall(r'{(.*?)}', path))


def get_dependent(
        *, path: t.Text,
        call: t.Callable[..., t.Any],
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
        use_cache: bool = True
) -> Dependent:
    """ 从调用对象获取依赖树

    @param path: 请求路径, 如: /items/{item_id}/?
    @param call: 调用对象
    @param name: 依赖名称
    @param security_scopes: 权限范围列表
    @param use_cache: 是否使用缓存?
    @return: Dependent
    """
    # 获取路径参数中的参数名集合,用于判断是否为路径参数
    path_field_names = get_path_param_names(path)
    # 重新为调用对象生成签名对象,主要反射所有参数的注解
    call_signature = get_typed_signature(call)
    dependent = Dependent(call=call, use_cache=use_cache, name=name, path=path)
    for param_name, param in call_signature.parameters.items():
        # 当参数默认值为依赖对象时,递归解析其dependent并注入
        if isinstance(param.default, params.Depended):
            kwargs = {'param': param, 'path': path,
                      'security_scopes': security_scopes}
            sub_dependent = get_param_sub_dependant(**kwargs)
            dependent.sub_dependents.append(sub_dependent)
            continue
        # 当参数注解为Request,Response,Service,Scope忽略
        if add_non_field_param(param=param, dependent=dependent):
            continue
        param_model_field = gen_param_field(param_name=param_name, param=param,
                                            default_field_info_class=params.Query)
        # 当参数名称存在于路径参数名集合中时,表示此字段为路径参数
        if param_name in path_field_names:
            is_scalar = is_scalar_field(param_model_field)
            is_scalar or logger.error(f'path params must one of scalar types')
            ignore_default = not isinstance(param.default, params.Path)
            param_model_field = gen_param_field(
                param=param, default_field_info_class=params.Path,
                param_name=param_name, ignore_default=ignore_default,
                param_type=params.ParamTypes.path
            )
            add_param_field(model_field=param_model_field, dependent=dependent)
        # 当参数为除了路径参数之外的其他标准字段则将其作为查询参数
        elif is_scalar_field(model_field=param_model_field):
            add_param_field(model_field=param_model_field, dependent=dependent)
        # 当参数注解类型为序列类且默认值为Query或Header实例时候
        elif isinstance(param.default, (params.Query, params.Header)
                        ) and is_scalar_sequence_field(param_model_field):
            add_param_field(model_field=param_model_field, dependent=dependent)
        # 除依赖,排除字段,路径字段,查询字段,多值查询/头部就算Body
        else:
            as_body = isinstance(param_model_field.field_info, params.Body)
            as_body or logger.error(f'param {param_model_field.name} can only be request body')
            dependent.body_fields.append(param_model_field)
    return dependent
