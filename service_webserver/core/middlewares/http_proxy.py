#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_core.core.service.entrypoint import Entrypoint
from werkzeug.middleware.http_proxy import ProxyMiddleware as BaseProxyMiddleware

if t.TYPE_CHECKING:
    # 由于其定义在存根文件所以需要在TYPE_CHECKING下
    from werkzeug.wsgi import WSGIApplication

from .base import BaseMiddleware


class HttpProxyMiddleware(BaseProxyMiddleware, BaseMiddleware):
    """ 请求代理中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication, producer: Entrypoint, **kwargs: t.Any) -> None:
        """ 初始化实例

        @param wsgi_app: 应用程序
        @param producer: 服务提供者
        @param kwargs: 命名参数
        """
        BaseProxyMiddleware.__init__(self, wsgi_app, **kwargs)
        BaseMiddleware.__init__(self, wsgi_app=wsgi_app, producer=producer)
