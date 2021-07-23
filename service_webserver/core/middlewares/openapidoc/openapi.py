#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import typing as t

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
        response_mimetype = response_class.mimetype
    for method in router.entrypoint.methods:
        metas_data = gen_openapi_metas(router, method)
        parameters: t.List[t.Dict[t.Text, t.Any]] = []

    return path, path_definitions, security_schemes


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
    for router in routers:
        result =
