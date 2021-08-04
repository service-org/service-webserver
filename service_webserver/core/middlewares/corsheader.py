#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from werkzeug.datastructures import Headers
from service_core.core.service.entrypoint import Entrypoint

if t.TYPE_CHECKING:
    # 由于其定义在存根文件所以需要在TYPE_CHECKING下
    from werkzeug.wsgi import WSGIApplication
    from werkzeug.wsgi import WSGIEnvironment
    from werkzeug.wrappers.response import StartResponse

from .base import Middleware

# 字典头部
HTTPDictHeaders = t.Mapping[str, t.Union[str, int, t.Iterable[t.Union[str, int]]]]
# 元组头部
HTTPIterHeaders = t.Iterable[t.Tuple[str, t.Union[str, int]]]
# 响应头部
HttpHeaders = t.Optional[t.Union[HTTPDictHeaders, HTTPIterHeaders]]


class CorsHeaderMiddleware(Middleware):
    """ 跨越配置中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication, producer: Entrypoint,
                 headers: t.Optional[t.Dict[t.Text, t.Text]] = None) -> None:
        """ 初始化实例

        @param wsgi_app: 应用程序
        @param producer: 服务提供者
        @param headers: 跨域头部设置
        """
        super(CorsHeaderMiddleware, self).__init__(wsgi_app=wsgi_app, producer=producer)
        self.headers = headers or {}
        self.headers.setdefault('Access-Control-Allow-Origin', '*')
        self.headers.setdefault('Access-Control-Allow-Credentials', 'true')
        self.headers.setdefault('Access-Control-Allow-Headers', '*')
        self.headers.setdefault('Access-Control-Allow-Methods', '*')

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """

        def add_cors_headers(status: t.Text, headers: HttpHeaders, exc_info: t.Optional[t.Tuple] = None):
            """ 添加跨域头部

            @param status  : 响应状态
            @param headers : 头部信息
            @param exc_info: 异常信息
            """
            headers = Headers(headers)
            headers.extend(**self.headers)
            headers = list(headers)
            return start_response(status, headers, exc_info)

        return self.wsgi_app(environ, add_cors_headers)  # type: ignore
