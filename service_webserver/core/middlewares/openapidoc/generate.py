#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_green.core.green import cjson
from pydantic.schema import get_model_name_map
from service_webserver.core.openapi3.models import OpenAPI
from service_webserver.core.openapi3.encoder import jsonable_encoder
from service_webserver.core.entrypoints.webserver.consumer import ReqConsumer

from .path import gen_openapi_path
from .flat_models import get_flat_models
from .definitions import gen_openapi_model_definitions


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
    flat_models = get_flat_models(routers)
    model_name_map = get_model_name_map(flat_models)
    definitions = gen_openapi_model_definitions(flat_models, model_name_map)
    for consumer in routers:
        path, security_schemes, path_definitions = gen_openapi_path(consumer, model_name_map)
        path and paths.setdefault(consumer.path, {}).update(path)
        security_schemes and components.setdefault('SecuritySchemes', {}).update(security_schemes)
        path_definitions and definitions.update(path_definitions)
    components['schemas'] = {k: definitions[k] for k in sorted(definitions)}
    data.update({'paths': paths, 'tags': api_tags, 'components': components})
    return cjson.dumps(jsonable_encoder(OpenAPI(**data), exclude_none=True))
