#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic.schema import TypeModelSet
from pydantic.schema import TypeModelOrEnum
from pydantic.schema import model_process_schema
from service_webserver.core.openapi3.encoder import jsonable_encoder
from service_webserver.constants import DEFAULT_DEFINITIONS_REF_PREFIX
from service_webserver.core.openapi3.generate.depent.models import Dependent


def gen_openapi_security_definitions(
        flat_dependent: Dependent
) -> t.Tuple[t.Dict[t.Text, t.Any], t.List[t.Dict[t.Text, t.Any]]]:
    """ 从扁平模型获取安全定义
    @param flat_dependent: 依赖对象
    @return: t.Tuple[t.Dict[t.Text, t.Any], t.List[t.Dict[t.Text, t.Any]]]
    """
    security_definitions: t.Dict[t.Text, t.Any] = {}
    security_scopes: t.List[t.Dict[t.Text, t.Any]] = []
    for security_scheme in flat_dependent.security_schemes:
        security_definition = jsonable_encoder(security_scheme.scheme.model,
                                               by_alias=True, exclude_none=True)
        security_name = security_scheme.scheme.scheme_name
        security_definitions[security_name] = security_definition
        security_scopes.append({security_name: security_scheme.scopes})
    return security_definitions, security_scopes


def gen_openapi_model_definitions(
        flat_models: TypeModelSet,
        model_name_map: Dict[TypeModelOrEnum, t.Text]
) -> t.Dict[t.Text, t.Any]:
    """ 从扁平模型获取模型定义

    @param flat_models: 依赖对象
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
