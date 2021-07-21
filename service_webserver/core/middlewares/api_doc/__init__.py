#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pkg_resources import get_distribution
from service_core.core.decorator import AsLazyProperty
from service_webserver.core.middlewares.base import BaseMiddleware

if t.TYPE_CHECKING:
    from werkzeug.wsgi import WSGIApplication
    from werkzeug.wsgi import WSGIEnvironment
    from werkzeug.wrappers.response import StartResponse
    from service_core.core.service.entrypoint import BaseEntrypoint

    # 入口类型
    Entrypoint = t.TypeVar('Entrypoint', bound=BaseEntrypoint)

server = get_distribution('service-webserver')


class ApiDocMiddleware(BaseMiddleware):
    """ Api doc 中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication, producer: Entrypoint,
                 title: t.Text = '', description: t.Text = '',
                 version: t.Text = server.version,
                 openapi_version: t.Text = '3.0.2',
                 openapi_url: t.Optional[t.Text] = '/openapi.json',
                 openapi_tags: t.Optional[t.List[t.Dict[t.Text: t.Any]]] = None,
                 redoc_url: t.Optional[t.Text] = '/redoc',
                 swagger_url: t.Optional[t.Text] = '/swagger',
                 servers: t.Optional[t.List[t.Dict[t.Text: t.Union[t.Text, t.Any]]]] = None,
                 ) -> None:
        """ 初始化实例

        @param wsgi_app: 请求处理函数
        @param title: Api文档标题
        @param description: Api文档描述
        @param version: Api文档版本
        @param openapi_version: OpenApi版本
        @param openapi_url: OpenApi接口地址
        @param openapi_tags: OpenApi聚合标签
        @param redoc_url: redoc文档的url地址
        @param swagger_url: swagger文档地址
        @param servers: 下拉选择的目标服务器
        """
        self._title = title
        self._description = description
        self.version = version
        self.openapi_version = openapi_version
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags or []
        self.redoc_url = redoc_url
        self.swagger_url = swagger_url
        self.servers = servers or []
        super(ApiDocMiddleware, self).__init__(wsgi_app=wsgi_app, producer=producer)

    @AsLazyProperty
    def title(self) -> t.Text:
        """ Api文档标题

        @return: t.Text:
        """
        return self._title or self.producer.container.service.name

    @AsLazyProperty
    def description(self) -> t.Text:
        """ Api文档描述

        @return: t.Text
        """
        return self._description or self.producer.container.service.desc

    @AsLazyProperty
    def routers(self) -> t.Dict[t.Text, t.Callable]:
        """ 已注册路由表

        @return: t.Dict[t.Text, t.Callable]
        """
        return self.producer.container.service.router_mapping

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        # start_response('200 Ok', [('Content-Type', 'application/json')])
        # return [b'200 Ok']
        return self.wsgi_app(environ, start_response)
