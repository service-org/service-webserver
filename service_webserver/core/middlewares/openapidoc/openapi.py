#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import typing as t

from pydantic.schema import field_schema
from service_green.core.green import json
from pydantic.schema import get_model_name_map
from service_webserver.core.openapi import params
from pydantic.schema import get_flat_models_from_fields
from service_webserver.core.openapi.models import OpenAPI
from service_webserver.core.openapi.constants import REF_PREFIX
from service_webserver.core.openapi.encoder import jsonable_encoder
from service_webserver.core.openapi.helper import get_flat_dependant

if t.TYPE_CHECKING:
    # https://swagger.io/specification/#paths-object
    OpenApiPath = t.Dict[t.Text, t.Any]
    OpenApiPathDefinitions = t.Dict[t.Text, t.Any]
    # https://swagger.io/specification/#components-object
    OpenApiSecuritySchemes = t.Dict[t.Text, t.Any]

from collections import namedtuple

Router = namedtuple('Router', ['name', 'entrypoint', 'view'])

__all__ = ['get_openapi_payload']


def gen_openapi_metas(router: Router, method: t.Text) -> t.Dict[t.Text, t.Any]:
    """ 生成openapi元数据

    @param router: 路由对象
    @param method: 请求方法
    @return: t.Text
    """
    openapi_metas_data, method = {}, method.lower()
    if router.entrypoint.operation_id:
        operation_id = router.entrypoint.operation_id + '_' + method
        openapi_metas_data['operation_id'] = operation_id
    if router.entrypoint.deprecated:
        openapi_metas_data['deprecated'] = router.entrypoint.deprecated
    if router.entrypoint.tags:
        openapi_metas_data['tags'] = router.entrypoint.tags
    if router.entrypoint.description:
        openapi_metas_data['description'] = router.entrypoint.description
    if router.entrypoint.summary:
        openapi_metas_data['summary'] = router.entrypoint.summary
    return openapi_metas_data

def get_flat_params(dependant):
    flat_dependant = get_flat_dependant(dependant)
    return (
        flat_dependant.path_params
        + flat_dependant.query_params
        + flat_dependant.header_params
        + flat_dependant.cookie_params
    )


def get_openapi_operation_params(*, all_route_params):
    parameters = []
    for param in all_route_params:
        field_info = param.field_info
        field_info = t.cast(params.Param, field_info)
        parameter = {
            'name': param.alias,
            'in': field_info.in_.value,
            'required': param.required,
            'schema': field_schema(param, model_name_map={}, ref_prefix=REF_PREFIX)[0]
        }
        if field_info.description:
            parameter['description'] = field_info.description
        if field_info.example:
            parameter['example'] = field_info.example
        if field_info.examples:
            parameter['examples'] = field_info.examples
        if field_info.deprecated:
            parameter['deprecated'] = field_info.deprecated
        parameters.append(parameter)
    return parameters


def get_openapi_paths(router: Router) -> t.Tuple[OpenApiPath, OpenApiPathDefinitions, OpenApiSecuritySchemes]:
    """ 获取openapi路径

    @param router: 路由对象
    @return: t.Tuple[OpenApiPath, OpenApiPathDefinitions, OpenApiSecuritySchemes]
    """
    path: t.Dict[t.Text, t.Any] = {}
    path_definitions: t.Dict[t.Text, t.Any] = {}
    security_schemes: t.Dict[t.Text, t.Any] = {}
    # 自动忽略掉不想暴露在支持openapi的文档的接口
    if not router.entrypoint.include_in_doc:
        return path, path_definitions, security_schemes
    else:
        response_class = router.entrypoint.response_class
        # response_mimetype = response_class.mimetype
    for method in router.entrypoint.methods:
        operator = gen_openapi_metas(router, method)
        parameters: t.List[t.Dict[t.Text, t.Any]] = []
        # flat_dependant = get_flat_dependant(router.entrypoint.dependant)
        all_route_params = get_flat_params(router.entrypoint.dependant)
        operation_params = get_openapi_operation_params(all_route_params=all_route_params)
        parameters.extend(operation_params)
        if parameters:
            operator['parameters'] = parameters
        operator['responses'] = {}
        # 省略掉其它的参数解析
        path[method.lower()] = operator
    return path, security_schemes, path_definitions


def get_flat_models_from_routers(routes):
    body_fields = []
    responses = []
    request_fields = []
    for route in routes:
        name, entrypoint, view = route.name, route.entrypoint, route.view
        if not entrypoint.include_in_doc:
            continue
        if entrypoint.body_field:
            body_fields.append(entrypoint.body_field)
        if entrypoint.response_field:
            request_fields.append(entrypoint.response_field)
        params = get_flat_params(entrypoint.dependant)
        request_fields.extend(params)
    return get_flat_models_from_fields(body_fields + responses + request_fields)


def get_openapi_payload(title: t.Text,
                        routers: t.Sequence[Router],
                        description: t.Text = '',
                        version: t.Text = '0.0.1',
                        openapi_version: t.Text = '3.0.3',
                        api_tags: t.Optional[t.List[t.Dict[t.Text: t.Any]]] = None,
                        servers: t.Optional[t.List[t.Dict[t.Text: t.Union[t.Text, t.Any]]]] = None):
    """ 获取openapi载体 """
    # https://swagger.io/specification/#info-object
    info = {'title': title, 'version': version}
    description and info.update({'description': description})
    # https://swagger.io/specification/#openapi-object
    data = {'openapi': openapi_version, 'info': info}
    # https://swagger.io/specification/#server-object
    servers and data.update({'servers': servers})
    # https://swagger.io/specification/#components-object
    components: t.Dict[t.Text, t.Dict[t.Text, t.Any]] = {}
    # https://swagger.io/specification/#paths-object
    paths: t.Dict[t.Text, t.Dict[t.Text, t.Any]] = {}
    # 主要用于查找所有定义的模型
    flat_models = {}
    model_name_map = {}
    definitions = {}
    for router in routers:
        name, entrypoint, view = router.name, router.entrypoint, router.view
        print('!' * 100)
        print(entrypoint.dependant)
        print('!' * 100)
        result = get_openapi_paths(router)
        if result:
            path, security_schemes, path_definitions = result
            if path:
                paths.setdefault(entrypoint.path, {}).update(path)
            if security_schemes:
                components.setdefault('SecuritySchemes', {}).update(security_schemes)
            if path_definitions:
                definitions.update(path_definitions)
    if definitions:
        components['schemas'] = {k: definitions[k] for k in sorted(definitions)}
    if components:
        data['components'] = components
    data['paths'] = paths
    if api_tags:
        data['tags'] = api_tags
    print('!' * 100)
    import pprint
    pprint.pprint(data)
    data = jsonable_encoder(OpenAPI(**data), by_alias=True, exclude_none=True)
    return json.dumps(data)
