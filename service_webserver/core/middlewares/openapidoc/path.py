#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import inspect
import http.client
import typing as t

from pydantic.fields import Undefined
from pydantic.fields import ModelField
from pydantic.schema import field_schema
from pydantic.schema import TypeModelOrEnum
from service_webserver.core.response import JsonResponse
from service_webserver.core.openapi3.generate.depent import params
from service_webserver.core.openapi3.encoder import jsonable_encoder
from service_webserver.constants import DEFAULT_METHODS_THAT_WITH_BODY
from service_webserver.constants import DEFAULT_DEFINITIONS_REF_PREFIX
from service_webserver.constants import DEFAULT_CODE_THAT_WITH_NO_BODY
from service_webserver.constants import DEFAULT_ALL_STATUS_CODE_RANGES
from service_webserver.core.openapi3.generate.update import deep_update_dict
from service_webserver.core.entrypoints.webserver.consumer import ReqConsumer
from service_webserver.core.openapi3.generate.depent.checks import is_subclass
from service_webserver.core.openapi3.generate.depent.helper import get_flat_dependent

from .flat_params import get_flat_params
from .definitions import gen_openapi_security_definitions


def gen_openapi_path_response_schema(
        response_field: ModelField,
        *,
        model_name_map: t.Dict[TypeModelOrEnum, t.Text]
) -> t.Dict[t.Text, t.Any]:
    """ 生成openapi path的response schema

    @param response_field: 响应字段
    @param model_name_map: 模型映射
    @return: t.Dict[t.Text, t.Any]
    """
    kwargs = {
        'model_name_map': model_name_map,
        'ref_prefix': DEFAULT_DEFINITIONS_REF_PREFIX
    }
    if not response_field:
        response_schema = {}
    else:
        r = field_schema(response_field, **kwargs)
        response_schema = r[0]
    return response_schema


def gen_openapi_path_responses(
        *, router: ReqConsumer,
        model_name_map: t.Dict[TypeModelOrEnum, t.Text]
) -> t.Dict[t.Text, t.Any]:
    """ 生成openapi path的responses

    @param router: 路由对象
    @param model_name_map: 模型映射
    @return: t.Dict[t.Text, t.Any]
    """
    response_class = router.response_class
    responses_definition: t.Dict[t.Text, t.Any] = {}
    response_class_media_type = response_class.mimetype
    if router.status_code is not None:
        response_code = str(router.status_code)
    else:
        response_class_signature = inspect.signature(response_class.__init__)
        response_code_param = response_class_signature.parameters.get('status')
        response_code = response_code_param.default
        is_int_response_code = isinstance(response_code, int)
        response_code = response_code if is_int_response_code else None
    responses_definition.setdefault(response_code, {}).update({
        'description': router.response_description
    })
    if response_class_media_type and response_code not in DEFAULT_CODE_THAT_WITH_NO_BODY:
        if not is_subclass(response_class, JsonResponse):
            response_schema = {'type': 'string'}
        else:
            response_schema = gen_openapi_path_response_schema(
                router.response_field, model_name_map=model_name_map
            )
        c = responses_definition.setdefault(response_code, {}).setdefault('content', {})
        c.setdefault(response_class_media_type, {}).update({'schema': response_schema})
    if response_class_media_type and router.other_response:
        for status_code, response in router.other_response.items():
            this_response = response.copy()
            this_response.pop('model', None)
            curr_status_code = str(status_code).upper()
            curr_status_code = 'default' if this_response == 'DEFAULT' else curr_status_code
            curr_response = responses_definition.setdefault(curr_status_code, {})
            curr_response_field = router.other_response_fields.get(curr_status_code)
            curr_response_schema = gen_openapi_path_response_schema(curr_response_field,
                                                                    model_name_map=model_name_map)
            m = curr_response.setdefault('content', {}).setdefault(response_class_media_type, {})
            s = m.setdefault('schema', {})
            deep_update_dict(s, curr_response_schema)
            curr_status_code_desc = (
                    DEFAULT_ALL_STATUS_CODE_RANGES.get(str(curr_status_code).upper())
                    or
                    http.client.responses.get(int(status_code))
            )
            curr_response_description = (
                    this_response.get('description') or curr_response.get('description')
                    or
                    curr_status_code_desc
            )
            deep_update_dict(curr_response, this_response)
            curr_response['description'] = curr_response_description
    return responses_definition


def gen_openapi_path_request_body(
        *, body_field: t.Optional[ModelField],
        model_name_map: t.Dict[TypeModelOrEnum, t.Text]
) -> t.Dict[t.Text, t.Any]:
    """ 生成openapi path的body

    @param body_field: body字段
    @param model_name_map: 模型映射
    @return: t.Optional[t.Dict[t.Text, t.Any]]
    """
    body_definition: t.Dict[t.Text, t.Any] = {}
    if not body_field:
        return body_definition
    body_schema, _, _ = field_schema(
        body_field, model_name_map=model_name_map,
        ref_prefix=DEFAULT_DEFINITIONS_REF_PREFIX
    )
    body_field_info = t.cast(params.Body, body_field.field_info)
    body_media_type = body_field_info.media_type
    body_required = body_field.required
    body_required and body_definition.setdefault('required', body_required)
    body_content: t.Dict[t.Text, t.Any] = {'schema': body_schema}
    if body_field_info.examples:
        body_content['examples'] = jsonable_encoder(body_field_info.examples)
    elif body_field_info.example != Undefined:
        body_content['example'] = jsonable_encoder(body_field_info.example)
    body_definition['content'] = {body_media_type: body_content}
    return body_definition


def gen_openapi_path_parameters(
        *, flat_params: t.Sequence[ModelField],
        model_name_map: t.Dict[TypeModelOrEnum, t.Text]
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
        field_info.example != Undefined and parameter.update({
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
        model_name_map: t.Dict[TypeModelOrEnum, t.Text]
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
    for method in router.methods:
        path_definition = gen_openapi_path_metadata(router=router, method=method)
        flat_dependent = get_flat_dependent(router.dependent, skip_repeats=True)
        security_definitions, security_scopes = gen_openapi_security_definitions(
            flat_dependent=flat_dependent
        )
        security_scopes and path_definition.setdefault('security', []).extend(security_scopes)
        security_definitions and security_schemes.update(security_definitions)
        flat_params = get_flat_params(router.dependent)
        path_parameters = gen_openapi_path_parameters(
            flat_params=flat_params, model_name_map=model_name_map
        )
        path_parameters and path_definition.setdefault('parameters', []).extend(path_parameters)
        path_request_body = {}
        if method in DEFAULT_METHODS_THAT_WITH_BODY:
            path_request_body = gen_openapi_path_request_body(
                body_field=router.body_field, model_name_map=model_name_map
            )
        path_request_body and path_definition.setdefault('requestBody', {}).update(path_request_body)
        path_responses = gen_openapi_path_responses(
            router=router, model_name_map=model_name_map
        )
        path_responses and path_definition.setdefault('responses', {}).update(path_responses)
        path[method.lower()] = path_definition
    path = {k: v for k, v in sorted(path.items(), key=lambda item: item[0])}
    return path, security_schemes, path_definitions
