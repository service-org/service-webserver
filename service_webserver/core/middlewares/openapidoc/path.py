#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic.fields import ModelField
from pydantic.schema import field_schema
from pydantic.schema import TypeModelOrEnum
from service_webserver.core.openapi3.generate.depent import params
from service_webserver.constants import DEFAULT_METHODS_THAT_WITH_BODY
from service_webserver.constants import DEFAULT_DEFINITIONS_REF_PREFIX
from service_webserver.core.entrypoints.webserver.consumer import ReqConsumer
from service_webserver.core.openapi3.generate.depent.helper import get_flat_dependent

from .flat_params import get_flat_params
from .definitions import gen_openapi_security_definitions

def gen_openapi_path_request_body(
        *, body_field: t.Optional[ModelField],
        model_name_map: Dict[TypeModelOrEnum, t.Text]
) -> t.Optional[t.Dict[t.Text, t.Any]]:
    """ 生成openapi path的body

    @param body_field: body字段
    @param model_name_map: 模型映射
    @return: t.Optional[t.Dict[t.Text, t.Any]]
    """
    pass


def gen_openapi_path_parameters(
        *, flat_params: t.Sequence[ModelField],
        model_name_map: Dict[TypeModelOrEnum, t.Text]
) -> t.List[t.Dict[t.Text, t.Any]]:
    """ 生成openapi path的参数

    @param flat_params: 所有字段
    @param model_name_map: 模型映射
    @return: t.List[t.Dict[t.Text, t.Any]]
    """
    parameters = []
    for param in flat_params:
        field_info = param.field_info
        field_info = t.cast(params.Param, field_info)
        filed_schema_data = field_schema(
            param, model_name_map=model_name_map,
            ref_prefix=DEFAULT_DEFINITIONS_REF_PREFIX
        )
        parameter = {'name': param.alias,
                     'in': field_info.in_.value,
                     'required': param.required,
                     'schema': filed_schema_data[0]}
        field_info.example and parameter.update({
            'example': field_info.example
        })
        field_info.examples and parameter.update({
            'examples': field_info.examples
        })
        field_info.deprecated and parameter.update({
            'deprecated': field_info.deprecated
        })
        field_info.description and parameter.update({
            'description': field_info.description
        })
        parameters.append(parameter)
    return parameters


def gen_openapi_path_metadata(*, router: ReqConsumer, method: t.Text) -> t.Dict[t.Text, t.Any]:
    """ 生成openapi path元数据

    @param router: 路由对象
    @param method: 请求方法
    @return: t.Text
    """
    metadata, method = {}, method.lower()
    if router.operation_id:
        operation_id = router.operation_id + '_' + method
        metadata['operation_id'] = operation_id
    if router.deprecated:
        metadata['deprecated'] = router.deprecated
    if router.tags:
        metadata['tags'] = router.tags
    if router.description:
        metadata['description'] = router.description
    if router.summary:
        metadata['summary'] = router.summary
    return metadata


def gen_openapi_path(
        router: ReqConsumer,
        model_name_map: Dict[TypeModelOrEnum, t.Text]
) -> t.Tuple[t.Dict[t.Text, t.Any], t.Dict[t.Text, t.Any], t.Dict[t.Text, t.Any]]:
    """ 获取openapi的路径信息

    @param router: 路由对象
    @param model_name_map: 模型映射
    @return: t.Tuple[OpenApiPath, OpenApiPathDefinitions, OpenApiSecuritySchemes]
    """
    path: t.Dict[t.Text, t.Any] = {}
    path_definitions: t.Dict[t.Text, t.Any] = {}
    security_schemes: t.Dict[t.Text, t.Any] = {}
    # 自动忽略掉不想暴露在支持openapi的文档的接口
    if not router.include_in_doc:
        return path, path_definitions, security_schemes
    else:
        response_class = router.response_class
        response_media_type = response_class.mimetype
    for method in router.methods:
        path_definition = gen_openapi_path_metadata(router=router, method=method)
        flat_dependent = get_flat_dependent(router.dependent, skip_repeats=True)
        security_definitions, security_scopes = gen_openapi_security_definitions(
            flat_dependent=flat_dependent
        )
        path_definition.setdefault('security', security_scopes)
        security_definitions and security_schemes.update(security_definitions)
        flat_params = get_flat_params(router.dependent)
        path_parameters = gen_openapi_path_parameters(
            flat_params=flat_params, model_name_map=model_name_map
        )
        path_definition.setdefault('parameters', path_parameters)
        if method in DEFAULT_METHODS_THAT_WITH_BODY:
            pass
    return path, security_schemes, path_definitions

