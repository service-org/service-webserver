#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t
import werkzeug.exceptions
from werkzeug.wrappers import Request

if t.TYPE_CHECKING:
    from werkzeug.wrappers.response import StartResponse
    from werkzeug.wrappers.request import WSGIEnvironment

    from .producer import ReqProducer

    # 生产者类型
    Producer = t.TypeVar('Producer', bound=ReqProducer)


class WsgiApp(object):
    """ Wsgi Application """

    def __init__(self, producer: Producer) -> None:
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
