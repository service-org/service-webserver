#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from werkzeug.middleware.shared_data import SharedDataMiddleware as BaseSharedDataMiddleware

if t.TYPE_CHECKING:
    from werkzeug.wsgi import WSGIApplication
    from service_core.core.service.entrypoint import BaseEntrypoint

    # 入口类型
    Entrypoint = t.TypeVar('Entrypoint', bound=BaseEntrypoint)

from .base import BaseMiddleware


class ShareDataMiddleware(BaseSharedDataMiddleware, BaseMiddleware):
    """ 静态文件中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication, producer: Entrypoint, **kwargs: t.Any) -> None:
        """ 初始化实例

        @param wsgi_app: 应用程序
        @param producer: 服务提供者
        @param kwargs: 命名参数
        """
        BaseSharedDataMiddleware.__init__(self, wsgi_app, **kwargs)
        BaseMiddleware.__init__(self, wsgi_app=wsgi_app, producer=producer)
