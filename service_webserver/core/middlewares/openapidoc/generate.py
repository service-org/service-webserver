#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import enum
import typing as t

from pydantic.schema import field_schema
from service_green.core.green import cjson
from pydantic.schema import get_model_name_map
from service_webserver.core.openapi3.models import OpenAPI
from service_webserver.core.openapi3.generate.depent import params
from service_webserver.core.openapi3.encoder import jsonable_encoder
from service_webserver.core.openapi3.generate.depent.models import Dependent
from service_webserver.core.entrypoints.webserver.consumer import ReqConsumer

from .path import gen_openapi_path
from .flat_models import get_flat_models
from .definitions import gen_openapi_model_definitions
from .definitions import gen_openapi_security_definitions

def get_openapi_json(
        title: t.Text,
        routers: t.Sequence[ReqConsumer],
        description: t.Text = '',
        version: t.Text = '0.0.1',
        openapi_version: t.Text = '3.0.3',
        api_tags: t.Optional[t.List[t.Dict[t.Text: t.Any]]] = None,
        servers: t.Optional[t.List[t.Dict[t.Text: t.Union[t.Text, t.Any]]]] = None
) -> t.Text:
    """ 获取openapi.json """
    # https://swagger.io/specification/#info-object
    info = {'title': title, 'version': version}
    description and info.update({'description': description})
    # https://swagger.io/specification/#openapi-object
    data = {'openapi3': openapi_version, 'info': info}
    # https://swagger.io/specification/#server-object
    servers and data.update({'servers': servers})
    # https://swagger.io/specification/#components-object
    components: t.Dict[t.Text, t.Dict[t.Text, t.Any]] = {}
    # https://swagger.io/specification/#paths-object
    paths: t.Dict[t.Text, t.Dict[t.Text, t.Any]] = {}
    # 主要用于查找所有定义的模型
    flat_models = get_flat_models(routers)
    model_name_map = get_model_name_map(flat_models)
    definitions = gen_openapi_model_definitions(flat_models, model_name_map)
    for consumer in routers:
        path_data = gen_openapi_path(consumer)
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
