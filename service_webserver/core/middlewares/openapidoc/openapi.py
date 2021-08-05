#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import enum
import re
import typing as t

from collections import namedtuple
from pydantic.fields import BaseModel
from pydantic.fields import ModelField
from pydantic.schema import field_schema
from pydantic.schema import TypeModelSet
from service_green.core.green import cjson
from pydantic.schema import TypeModelOrEnum
from pydantic.schema import get_model_name_map
from pydantic.schema import model_process_schema
from service_webserver.core.openapi import params
from pydantic.schema import get_flat_models_from_fields
from service_webserver.core.inspection.models import OpenAPI
from service_webserver.core.openapi import get_flat_dependent
from service_webserver.core.inspection.depent import Dependent
from service_webserver.constants import DEFAULT_DEFINITIONS_REF_PREFIX

Router = namedtuple('Router', ['name', 'entrypoint', 'view'])

__all__ = ['get_openapi_payload']


def gen_openapi_operation_metadata(*, router: Router, method: t.Text) -> t.Dict[t.Text, t.Any]:
    """ 生成openapi操作元数据

    @param router: 路由对象
    @param method: 请求方法
    @return: t.Text
    """
    openapi_operation_metadata, method = {}, method.lower()
    if router.entrypoint.operation_id:
        operation_id = router.entrypoint.operation_id + '_' + method
        openapi_operation_metadata['operation_id'] = operation_id
    if router.entrypoint.deprecated:
        openapi_operation_metadata['deprecated'] = router.entrypoint.deprecated
    if router.entrypoint.tags:
        openapi_operation_metadata['tags'] = router.entrypoint.tags
    if router.entrypoint.description:
        openapi_operation_metadata['description'] = router.entrypoint.description
    if router.entrypoint.summary:
        openapi_operation_metadata['summary'] = router.entrypoint.summary
    return openapi_operation_metadata


def get_openapi_security_definitions(
        flat_dependent: Dependent
) -> t.Tuple[t.Dict[t.Text, t.Any], t.List[t.Dict[t.Text, t.Any]]]:
    """

    @param flat_dependent:
    @return:
    """


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


def get_openapi_path(
        router: Router
) -> t.Tuple[t.Dict[t.Text, t.Any], t.Dict[t.Text, t.Any], t.Dict[t.Text, t.Any]]:
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
        response_media_type = response_class.mimetype
    for method in router.entrypoint.methods:
        operation_metadata = gen_openapi_operation_metadata(router=router, method=method)
        parameters: t.List[t.Dict[t.Text, t.Any]] = []
        flat_dependent = get_flat_dependent(router.entrypoint.dependent, skip_repeats=True)
        security_definitions, operation_security =
        all_route_params = get_flat_params(router.entrypoint.dependent)
        operation_params = get_openapi_operation_params(all_route_params=all_route_params)
        parameters.extend(operation_params)
        if parameters:
            operator['parameters'] = parameters
        operator['responses'] = {}
        # 省略掉其它的参数解析
        path[method.lower()] = operator
    return path, security_schemes, path_definitions


def get_flat_params(dependent: Dependent) -> t.List[ModelField]:
    """ 从依赖对象获取扁平化参数

    @param dependent: 依赖对象
    @return: t.List[ModelField]
    """
    flat_dependent = get_flat_dependent(dependent, skip_repeats=True)
    return (
            flat_dependent.path_fields
            + flat_dependent.query_fields
            + flat_dependent.header_fields
            + flat_dependent.cookie_fields
    )


def get_flat_models_from_routers(routers: t.Sequence[Router]) -> t.Set[t.Union[t.Type[BaseModel], t.Type[enum.Enum]]]:
    """ 从路由中获取所有的模型

    @param routers: 路由列表
    @return: t.Set[t.Union[t.Type[BaseModel], t.Type[enum.Enum]]]
    """
    all_fields_from_routers: t.List[ModelField] = []
    body_fields_from_routers: t.List[ModelField] = []
    request_fields_from_routers: t.List[ModelField] = []
    response_fields_from_routers: t.List[ModelField] = []
    for router in routers:
        entrypoint = router.entrypoint
        if not entrypoint.include_in_doc:
            continue
        if entrypoint.body_field:
            fields = entrypoint.body_field
            body_fields_from_routers.append(fields)
        if entrypoint.response_field:
            fields = entrypoint.response_field
            response_fields_from_routers.append(fields)
        if entrypoint.other_response_fields:
            fields = entrypoint.other_response_fields.values()
            response_fields_from_routers.extend(fields)
        request_fields = get_flat_params(entrypoint.dependent)
        request_fields_from_routers.extend(request_fields)
    all_fields_from_routers += body_fields_from_routers
    all_fields_from_routers += request_fields_from_routers
    all_fields_from_routers += response_fields_from_routers
    return get_flat_models_from_fields(
        all_fields_from_routers, known_models=set()
    )


def get_model_definitions(
        flat_models: TypeModelSet,
        model_name_map: Dict[TypeModelOrEnum, t.Text]
) -> t.Dict[t.Text, t.Any]:
    """ 从扁平模型获取模型定义

    @param flat_models: 模型集合
    @param model_name_map: 名称映射
    @return: t.Dict[t.Text, t.Any]
    """
    definitions: t.Dict[t.Text, t.Any] = {}
    for model in flat_models:
        r = model_process_schema(
            model, model_name_map=model_name_map,
            ref_prefix=DEFAULT_DEFINITIONS_REF_PREFIX
        )
        m_schema, m_definitions, m_nested_models = r
        definitions.update(m_definitions)
        model_name = model_name_map[model]
        definitions[model_name] = m_schema
    return definitions


def get_openapi_payload(
        title: t.Text,
        routers: t.Sequence[Router],
        description: t.Text = '',
        version: t.Text = '0.0.1',
        openapi_version: t.Text = '3.0.3',
        api_tags: t.Optional[t.List[t.Dict[t.Text: t.Any]]] = None,
        servers: t.Optional[t.List[t.Dict[t.Text: t.Union[t.Text, t.Any]]]] = None
) -> t.Text:
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
    flat_models = get_flat_models_from_routers(routers)
    model_name_map = get_model_name_map(flat_models)
    definitions = get_model_definitions(flat_models, model_name_map)
    for router in routers:
        entrypoint = router.entrypoint
        path_data = get_openapi_path(router)
        if path_data:
            path, security_schemes, path_definitions = path_data
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
