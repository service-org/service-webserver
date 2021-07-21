#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t


def gen_openapi_json(*,
                    title: t.Text,
                    version: t.Text,
                    description: t.Optional[t.Text] = None,
                    openapi_version: t.Text = '3.0.2',
                    routers: t.Dict[t.Text, t.Any],
                    tags: t.Optional[t.List[t.Dict[t.Text, t.Any]]] = None,
                    servers: t.Optional[t.List[t.Dict[t.Text, t.Union[t.Text, t.Any]]]] = None
                    ) -> t.Dict[t.Text, t.Any]:
    """ 生成 OpenAPI Specification

    @param title: Api文档标题
    @param version: Api文档版本
    @param description: Api文档描述
    @param openapi_version: OpenApi版本
    @param routers: 所有路由信息
    @param tags: OpenApi聚合标签
    @param servers: 下拉选择的目标服务器
    @return: t.Dict[t.Text, t.Any]
    """
    info = {'title': title, 'version': version}
    description and info.update({'description': description})
    output = {'openapi': openapi_version, 'info': info}
    servers and output.update({'servers': servers})
    components: t.Dict[t.Text, t.Dict[t.Text, t.Any]] = {}
    paths: t.Dict[t.Text, t.Dict[t.Text, t.Any]] = {}
