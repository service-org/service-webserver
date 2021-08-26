#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from werkzeug.wrappers import Request
from service_core.core.decorator import AsLazyProperty
from service_core.core.service.entrypoint import Entrypoint
from service_webserver.core.middlewares.base import BaseMiddleware
from service_webserver.core.openapi3.generate.assets import get_redoc_html
from service_webserver.core.openapi3.generate.assets import get_swagger_ui_html
from service_webserver.core.openapi3.generate.assets import get_swagger_ui_oauth2_redirect_html

if t.TYPE_CHECKING:
    # 由于其定义在存根文件所以需要在TYPE_CHECKING下
    from werkzeug.wsgi import WSGIApplication
    from werkzeug.wsgi import WSGIEnvironment
    from werkzeug.wrappers.response import StartResponse

from .generate import get_openapi_json


class OpenApiDocMiddleware(BaseMiddleware):
    """ OpenApi doc 中间件类 """

    def __init__(
            self, *, wsgi_app: WSGIApplication, producer: Entrypoint,
            title: t.Text = '', description: t.Text = '',
            version: t.Text = '0.0.1',
            openapi_version: t.Text = '3.0.3',
            root_path: t.Optional[t.Text] = '',
            openapi_url: t.Optional[t.Text] = '/openapi3.json',
            api_tags: t.Optional[t.List[t.Dict[t.Text: t.Any]]] = None,
            redoc_url: t.Optional[t.Text] = '/redoc',
            swagger_url: t.Optional[t.Text] = '/swagger',
            swagger_ui_oauth2_init: t.Optional[t.Dict[t.Text, t.Any]] = None,
            swagger_ui_oauth2_redirect_url: t.Optional[t.Text] = '/swagger/oauth2-redirect',
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
        @param root_path: 前端有代理时需设置
        @param openapi_url: OpenApi接口地址
        @param api_tags: Api用于分组的标签
        @param redoc_url: redoc文档的url地址
        @param swagger_url: swagger文档地址
        @param servers: 下拉选择的目标服务器
        """
        self._title = title
        self._description = description
        self.version = version
        self.root_path = root_path
        self.openapi_version = openapi_version
        self.openapi_url = openapi_url
        self.api_tags = api_tags or []
        self.redoc_url = redoc_url
        self.swagger_url = swagger_url
        self.servers = servers or []
        self.swagger_ui_oauth2_init = swagger_ui_oauth2_init
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        super(OpenApiDocMiddleware, self).__init__(wsgi_app=wsgi_app, producer=producer)

    @AsLazyProperty
    def title(self) -> t.Text:
        """ 文档标题 """
        return self._title or self.producer.container.service.name

    @AsLazyProperty
    def description(self) -> t.Text:
        """ 文档描述 """
        return self._description or self.producer.container.service.desc

    @AsLazyProperty
    def redoc_ui_html(self) -> t.Text:
        """ redoc网页 """
        openapi_url = self.root_path + self.openapi_url
        return get_redoc_html(
            openapi_url=openapi_url,
            title=self.title + ' - Redoc'
        )

    @AsLazyProperty
    def swagger_ui_html(self) -> t.Text:
        """ swagger网页 """
        openapi_url = self.root_path + self.openapi_url
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=self.title + ' - Swagger UI',
            oauth2_init=self.swagger_ui_oauth2_init,
            oauth2_redirect_url=self.swagger_ui_oauth2_redirect_url
        )

    @AsLazyProperty
    def swagger_ui_oauth2_redirect_html(self):
        """ swagger oauth2 跳转页 """
        return get_swagger_ui_oauth2_redirect_html()

    @AsLazyProperty
    def openapi_json(self) -> t.Text:
        """ /openapi.json内容 """
        routers = self.producer.all_extensions
        return get_openapi_json(
            title=self.title,
            routers=routers,
            description=self.description,
            version=self.version,
            api_tags=self.api_tags,
            servers=self.servers,
            openapi_version=self.openapi_version,
        )

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        request = Request(environ)
        if request.path in (self.redoc_url, self.root_path + self.redoc_url):
            start_response('200 Ok', [('Content-Type', 'text/html')])
            return [self.redoc_ui_html]
        if request.path in (self.swagger_url, self.root_path + self.swagger_url):
            start_response('200 Ok', [('Content-Type', 'text/html')])
            return [self.swagger_ui_html]
        if request.path in (self.openapi_url, self.root_path + self.openapi_url):
            start_response('200 Ok', [('Content-Type', 'application/json')])
            return [self.openapi_json]
        return self.wsgi_app(environ, start_response)
