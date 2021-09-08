#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import sys
import typing as t

from http import HTTPStatus
from logging import getLogger
from service_webserver.core.response import HtmlResponse
from service_core.core.service.entrypoint import Entrypoint
from service_core.exchelper import gen_exception_description

if t.TYPE_CHECKING:
    # 由于其定义在存根文件所以需要在TYPE_CHECKING下
    from werkzeug.wsgi import WSGIApplication
    from werkzeug.wsgi import WSGIEnvironment
    from werkzeug.wrappers.response import StartResponse

from .base import BaseMiddleware

logger = getLogger(__name__)

# 字典头部
HTTPDictHeaders = t.Mapping[str, t.Union[str, int, t.Iterable[t.Union[str, int]]]]
# 元组头部
HTTPIterHeaders = t.Iterable[t.Tuple[str, t.Union[str, int]]]
# 响应头部
HttpHeaders = t.Optional[t.Union[HTTPDictHeaders, HTTPIterHeaders]]


class ExceptionMiddleware(BaseMiddleware):
    """ 异常处理中间件类 """

    def __init__(self, *, wsgi_app: WSGIApplication, producer: Entrypoint) -> None:
        """ 初始化实例

        @param wsgi_app: 应用程序
        @param producer: 服务提供者
        """
        super(ExceptionMiddleware, self).__init__(wsgi_app=wsgi_app, producer=producer)

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        try:
            return self.wsgi_app(environ, start_response)  # type: ignore
        except Exception:
            logger.error(f'middleware error', exc_info=True)
            exc_type, exc_value, exc_trace = sys.exc_info()
            data = gen_exception_description(exc_value)
            original = data['original']
            exc_name = exc_type.__name__
            original = f'{original} -' if original else original
            status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            payload = (
                f'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
                f'<title>{status} {exc_name}</title>'
                f'<h1>{data["exc_type"]}</h1>'
                f'<p>{original}{data["exc_errs"]}</p>'
            )
            headers = {'Content-Type': 'text/html; charset=utf-8'}
            response = HtmlResponse(payload, status, headers)
            return response(environ, start_response)  # type: ignore
