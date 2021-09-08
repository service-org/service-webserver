#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com
from __future__ import annotations

import re
import typing as t

from inspect import _empty
from inspect import Parameter
from logging import getLogger
from pydantic import create_model
from pydantic.fields import Required
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
from .typed import get_typed_signature

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
        body_fields=dependent.body_fields.copy(),
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
    body_fields = flat_dependent.body_fields
    if len(body_fields) == 0: return
    if len(body_fields) == 1 and not body_fields[0].field_info.embed: return body_fields[0]
    body_model, required = create_model(f'Body_{name}'), False
    for field in body_fields:
        field.field_info.embed = True
        # 收集的所有body字段加入模型对象中
        body_model.__fields__[field.name] = field
        # 有一个参数是必填则认为body必须的
        required = required or field.required
    file_field_media_types, form_field_media_types, body_field_media_types = [], [], []
    for field in body_fields:
        isinstance(field.field_info, params.File) and file_field_media_types.append(field.field_info.media_type)
        isinstance(field.field_info, params.Form) and form_field_media_types.append(field.field_info.media_type)
        isinstance(field.field_info, params.Body) and body_field_media_types.append(field.field_info.media_type)
    if len(file_field_media_types) > 0:
        body_field_info_class = params.File
        body_field_media_type = file_field_media_types[0]
        field_info = body_field_info_class(default=None, media_type=body_field_media_type)
        return gen_model_field(name='body', type_=body_model, required=required, field_info=field_info)
    if len(form_field_media_types) > 0:
        body_field_info_class = params.Form
        body_field_media_type = form_field_media_types[0]
        field_info = body_field_info_class(default=None, media_type=body_field_media_type)
        return gen_model_field(name='body', type_=body_model, required=required, field_info=field_info)
    if len(body_field_media_types) > 0:
        body_field_info_class = params.Body
        body_field_media_type = body_field_media_types[0]
        field_info = body_field_info_class(default=None, media_type=body_field_media_type)
        return gen_model_field(name='body', type_=body_model, required=required, field_info=field_info)


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


def gen_param_field(*, param: Parameter, param_type: t.Optional[params.ParamTypes] = None) -> ModelField:
    """ 生成响应用的模型字段

    @param param: 参数对象
    @param param_type: 参数类型
    @return: ModelField
    """
    field_info = param.default
    default_value = field_info.default
    field_info.in_ = param_type if isinstance(field_info, params.Param) else None
    annotation = param.annotation if param.annotation != param.empty else t.Any
    annotation = get_annotation_from_field_info(annotation, field_info, param.name)
    need_convert_underscores = getattr(field_info, 'convert_underscores', False)
    alias = param.name if not field_info.alias else field_info.alias
    alias = alias.replace('_', '-') if need_convert_underscores else alias
    required = (True if default_value == Required else False) or field_info.required
    return gen_model_field(**{
        'default': None if required else default_value, 'field_info': field_info,
        'name': param.name, 'alias': alias, 'type_': annotation, 'required': required,
    })


def add_non_field_param(*, param: Parameter, dependent: Dependent) -> t.Optional[bool]:
    """ 忽略掉特定注解的字段

    @param param: 参数对象
    @param dependent: 依赖对象
    @return: t.Optional[bool]
    """
    if is_subclass(param.annotation, SecurityScopes):
        dependent.security_scopes_field_name = param.name
        return True
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


def get_dependent(
        *, path: t.Text,
        call: t.Callable[..., t.Any],
        name: t.Optional[t.Text] = None,
        security_scopes: t.Optional[t.List[t.Text]] = None,
        use_cache: bool = True
) -> Dependent:
    """ 从调用对象获取依赖树

    @param path: 请求路径
    @param call: 调用对象
    @param name: 依赖名称
    @param security_scopes: 权限范围列表
    @param use_cache: 是否使用缓存?
    @return: Dependent
    """
    dependent = Dependent(use_cache=use_cache, call=call, name=name, path=path)
    for param_name, param in get_typed_signature(call).parameters.items():
        if isinstance(param.default, params.Depended):
            sub_dependent = get_param_sub_dependant(
                param=param, path=path, security_scopes=security_scopes
            )
            dependent.sub_dependents.append(sub_dependent)
            continue
        if add_non_field_param(param=param, dependent=dependent):
            continue
        if isinstance(param.default, params.Path):
            param_model_field = gen_param_field(
                param=param, param_type=params.ParamTypes.path
            )
            add_param_field(model_field=param_model_field, dependent=dependent)
        if isinstance(param.default, params.Query):
            param_model_field = gen_param_field(
                param=param, param_type=params.ParamTypes.query
            )
            add_param_field(model_field=param_model_field, dependent=dependent)
        if isinstance(param.default, params.Header):
            param_model_field = gen_param_field(
                param=param, param_type=params.ParamTypes.header
            )
            add_param_field(model_field=param_model_field, dependent=dependent)
        if isinstance(param.default, params.Cookie):
            param_model_field = gen_param_field(
                param=param, param_type=params.ParamTypes.cookie
            )
            add_param_field(model_field=param_model_field, dependent=dependent)
        if isinstance(param.default, params.Body):
            param_model_field = gen_param_field(param=param)
            dependent.body_fields.append(param_model_field)
    return dependent
