#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from werkzeug.wrappers import Request
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

from .redoc import get_redoc_payload
from .swagger import get_swagger_payload
from .openapi import get_openapi_payload

server = get_distribution('service-webserver')


class OpenApiDocMiddleware(BaseMiddleware):
    """ OpenApi doc 中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication, producer: Entrypoint,
                 title: t.Text = '', description: t.Text = '',
                 version: t.Text = server.version,
                 openapi_version: t.Text = '3.0.3',
                 openapi_url: t.Optional[t.Text] = '/openapi.json',
                 api_tags: t.Optional[t.List[t.Dict[t.Text: t.Any]]] = None,
                 redoc_url: t.Optional[t.Text] = '/redoc',
                 swagger_url: t.Optional[t.Text] = '/swagger',
                 servers: t.Optional[t.List[t.Dict[t.Text: t.Union[t.Text, t.Any]]]] = None
                 ) -> None:
        """ 初始化实例

        doc: https://www.jianshu.com/p/5365ef83252a

        @param wsgi_app: Wsgi应用处理器
        @param producer: 服务真正提供者
        @param title: Api文档的标题
        @param description: Api文档描述
        @param version: Api文档的版本
        @param openapi_version: OpenApi版本
        @param openapi_url: OpenApi接口地址
        @param api_tags: Api用于分组的标签
        @param redoc_url: redoc文档的url地址
        @param swagger_url: swagger文档地址
        @param servers: 下拉选择的目标服务器
        """
        self._title = title
        self._description = description
        self.version = version
        self.openapi_version = openapi_version
        self.openapi_url = openapi_url
        self.api_tags = api_tags or []
        self.redoc_url = redoc_url
        self.swagger_url = swagger_url
        self.servers = servers or []
        super(OpenApiDocMiddleware, self).__init__(wsgi_app=wsgi_app, producer=producer)

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
    def routes(self) -> t.Dict[t.Text, t.Callable]:
        """ 已注册路由表

        @return: t.Dict[t.Text, t.Callable]
        """
        pass
        # return self.producer.container.service.router_mapping

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        request = Request(environ)
        if request.path == self.openapi_url:
            headers = [('Content-Type', 'application/json')]
            start_response('200 Ok', headers)
            response_data = get_openapi_payload()
            return [response_data]
        if request.path == self.swagger_url:
            headers = [('Content-Type', 'text/html')]
            start_response('200 Ok', headers)
            response_data = get_swagger_payload()
            return [response_data]
        if request.path == self.redoc_url:
            headers = [('Content-Type', 'text/html')]
            start_response('200 Ok', headers)
            response_data = get_redoc_payload()
            return [response_data]
        return self.wsgi_app(environ, start_response)
