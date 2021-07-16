#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import eventlet
import typing as t

if t.TYPE_CHECKING:
    from werkzeug.routing import Map
    from eventlet.wsgi import Server
    from eventlet.greenio.base import GreenSocket

from logging import getLogger
from werkzeug.routing import Map
from greenlet import GreenletExit
from eventlet import wsgi, wrap_ssl
from service_core.core.decorator import AsFriendlyFunc
from service_webserver.constants import WEBSERVER_CONFIG_KEY
from service_core.core.service.extension import ShareExtension
from service_core.core.service.extension import StoreExtension
from service_core.core.service.entrypoint import BaseEntrypoint
from service_webserver.constants import DEFAULT_WEBSERVER_MAX_CONNECTIONS

from .wsgi_app import WsgiApp

logger = getLogger(__name__)


class ReqProducer(BaseEntrypoint, ShareExtension, StoreExtension):
    """ 通用请求生产者类 """

    name = 'Producer'

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """ 初始化实例

        @param args  : 位置参数
        @param kwargs: 命名参数
        """
        self.gt = None
        # 停止标志 - 是否停止
        self.stopped = False
        self.wsgi_server = None
        self.wsgi_socket = None
        # 相关配置 - 监听地址
        self.listen_host = None
        self.listen_port = None
        # 相关配置 - 启动配置
        self.srv_options = {}
        self.ssl_options = {}
        # 相关配置 - 路由配置
        self.map_options = {}
        # 相关配置 - 最大连接
        self.max_connect = None
        BaseEntrypoint.__init__(self, *args, **kwargs)
        ShareExtension.__init__(self, *args, **kwargs)
        StoreExtension.__init__(self, *args, **kwargs)

    def setup(self) -> None:
        """ 生命周期 - 载入阶段

        @return: None
        """
        self.listen_host = self.container.service.host
        self.listen_port = self.container.service.port
        map_options = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.map_options', default={})
        self.map_options = map_options | self.map_options
        max_connect = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.max_connect', default=None)
        max_connect = max_connect or DEFAULT_WEBSERVER_MAX_CONNECTIONS
        self.max_connect = self.max_connect or max_connect
        srv_options = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.srv_options', default={})
        self.srv_options = srv_options | self.srv_options
        ssl_options = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.ssl_options', default={})
        self.ssl_options = ssl_options | self.srv_options

    def start(self) -> None:
        """ 生命周期 - 启动阶段

        @return: None
        """
        args, kwargs = (), {}
        tid = f'{self}.self_handle_connect'
        fun = self.spawn_handle_request_thread
        addr = (self.listen_host, self.listen_port)
        self.wsgi_socket = eventlet.listen(addr, backlog=self.max_connect)
        self.wsgi_socket.settimeout(None)
        self.wsgi_server = self.create_wsgi_server()
        self.gt = self.container.spawn_splits_thread(fun, args=args, kwargs=kwargs, tid=tid)

    def stop(self) -> None:
        """ 生命周期 - 停止阶段

        @return: None
        """
        self.stopped = True
        wait_func = AsFriendlyFunc(self.gt.kill, all_exception=(GreenletExit,))
        wait_func()

    def kill(self) -> None:
        """ 生命周期 - 强杀阶段

        @return: None
        """
        self.stopped = True
        wait_func = AsFriendlyFunc(self.gt.kill, all_exception=(GreenletExit,))
        wait_func()

    def create_urls_map(self) -> Map:
        """ 创建一个wsgi urls map

        @return: Map
        """
        return Map([e.rule for e in self.all_extensions], **self.map_options)

    def create_wsgi_app(self) -> t.Callable:
        """ 创建一个wsgi application

        @return: t.Callable
        """
        return WsgiApp(self).wsgi_app

    def create_wsgi_server(self) -> Server:
        """ 创建一个wsgi server

        @return: Server
        """
        wsgi_app = self.create_wsgi_app()
        # 根据配置选项中SSL选项判断是否启用HTTPS
        wsgi_socket = wrap_ssl(self.wsgi_socket, **self.ssl_options) if self.ssl_options else self.wsgi_socket
        return wsgi.Server(wsgi_socket, self.wsgi_socket.getsockname(), wsgi_app, **self.srv_options)

    def spawn_handle_request_thread(self) -> None:
        """ 创建专门处理请求的协程

        @return: None
        """
        fun = self.handle_request
        tid = f'{self}.self_handle_request'
        while not self.stopped:
            client, addr = self.wsgi_socket.accept()
            args = (client, addr)
            source_string = f'{addr[0]}:{addr[1]}'
            target_string = f'{self.listen_host}:{self.listen_port}'
            logger.debug(f'{source_string} connect to {target_string}')
            client.settimeout(self.wsgi_server.socket_timeout)
            self.container.spawn_splits_thread(fun, args=args, tid=tid)
        logger.debug(f'good bey ~')

    def handle_request(self, client: GreenSocket, addr: t.Tuple) -> None:
        """ 通过server调用app处理

        @param client: 客户端对象
        @param addr: 客户端的地址
        @return: None
        """
        connection = [addr, client, wsgi.STATE_IDLE]
        # 请求最终交由WsgiApp去处理
        self.wsgi_server.process_request(connection)
