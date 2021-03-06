#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t
import werkzeug.exceptions

from logging import getLogger
from service_webserver.core.request import Request

if t.TYPE_CHECKING:
    # ReqProducer引用了App,需防止循环引用
    from .producer import ReqProducer
    # 由于其定义在存根文件所以需要在TYPE_CHECKING下
    from werkzeug.wrappers.response import StartResponse
    from werkzeug.wrappers.request import WSGIEnvironment

logger = getLogger(__name__)


class WsgiApp(object):
    """ Wsgi Application """

    def __init__(self, producer: ReqProducer) -> None:
        """ 初始化实例

        @param producer: 请求生产者对象
        """
        self.producer = producer
        self.urls_map = producer.create_urls_map()

    def wsgi_app(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        request = Request(environ)
        url, data, form = request.url, request.data, request.form.to_dict()
        logger.debug(f'request {url} with data={data} form={form}')
        adapter = self.urls_map.bind_to_environ(environ)
        try:
            # 通过路由匹配到Rule再到对应的entrypoint入口
            entrypoint, path_group_dict = adapter.match()
            # 记录一下请求时匹配到的url路径中的关键字字典
            request.path_group_dict = path_group_dict
            # 触发entrypoint的handle_request处理请求
            response = entrypoint.handle_request(request)
            # 注意: handle_request必须返回一个Response
            return response(environ, start_response)
        except werkzeug.exceptions.HTTPException as response:
            # 注意: HTTPException其实也是一个Response
            return response(environ, start_response)

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> t.Iterable[bytes]:
        """ 请求处理器

        @param environ: 环境对象
        @param start_response: 响应对象
        @return: t.Iterable[bytes]
        """
        return self.wsgi_app(environ, start_response)
