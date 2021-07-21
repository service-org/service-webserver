#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pkg_resources import get_distribution
from service_webserver.core.middlewares.base import BaseMiddleware

if t.TYPE_CHECKING:
    from werkzeug.wsgi import WSGIApplication
    from werkzeug.wsgi import WSGIEnvironment
    from werkzeug.wrappers.response import StartResponse

server = get_distribution('service-webserver')


class ApiDocMiddleware(BaseMiddleware):
    """ Api doc 中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication,
                 title: t.Text = 'Service', description: t.Text = '',
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
        self.title = title
        self.description = description
        self.version = version
        self.openapi_version = openapi_version
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags or []
        self.redoc_url = redoc_url
        self.swagger_url = swagger_url
        self.servers = servers or []
        super(ApiDocMiddleware, self).__init__(wsgi_app=wsgi_app)

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        print('=' * 100)
        print(f'{self.__class__.__name__} called~')
        print('=' * 100)
        return self.wsgi_app(environ, start_response)
