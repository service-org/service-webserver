#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from werkzeug.wsgi import WSGIApplication
    from werkzeug.wsgi import WSGIEnvironment
    from werkzeug.wrappers.response import StartResponse


class BaseMiddleware(object):
    """ 中间件基类 """

    def __init__(self, *, wsgi_app: WSGIApplication, **kwargs: t.Any) -> None:
        """ 初始化实例

        @param wsgi_app: 应用程序
        @param kwargs: 命名参数
        """
        self.wsgi_app = wsgi_app

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        return self.wsgi_app(environ, start_response)
