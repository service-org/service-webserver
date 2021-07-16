#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import eventlet
import typing as t

from eventlet import wsgi
from eventlet import support
from eventlet import greenio
from eventlet import wrap_ssl
from logging import getLogger
from eventlet.green import socket
from greenlet import GreenletExit
from service_core.core.decorator import AsFriendlyFunc
from service_webserver.constants import WEBSERVER_CONFIG_KEY
from service_core.core.service.extension import ShareExtension
from service_core.core.service.extension import StoreExtension
from service_core.core.service.entrypoint import BaseEntrypoint
from service_webserver.constants import DEFAULT_WEBSERVER_MAX_CONNECTIONS

if t.TYPE_CHECKING:
    from werkzeug.routing import Map
    from eventlet.wsgi import Server
    from eventlet.greenthread import GreenThread
    from eventlet.greenio.base import GreenSocket

from werkzeug.routing import Map

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
        self.connections = {}
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
        ssl_options = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.ssl_options', default={})
        self.ssl_options = ssl_options | self.srv_options
        srv_options = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.srv_options', default={})
        self.srv_options = srv_options | self.srv_options
        self.srv_options.setdefault('log', logger)
        self.srv_options.setdefault('log_output', True)

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
        kill_func = AsFriendlyFunc(self.wsgi_socket.close, all_exception=(socket.error,))
        kill_func()
        kill_func = AsFriendlyFunc(self.gt.kill, all_exception=(GreenletExit,))
        kill_func()

    def kill(self) -> None:
        """ 生命周期 - 强杀阶段

        @return: None
        """
        self.stopped = True
        kill_func = AsFriendlyFunc(self.wsgi_socket.close, all_exception=(socket.error,))
        kill_func()
        kill_func = AsFriendlyFunc(self.gt.kill, all_exception=(GreenletExit,))
        kill_func()

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

    def _link_cleanup_connection(self, gt: GreenThread, connection: t.List):
        """ 请求处理完成时回调函数

        @param gt: 协程对象
        @param connection: 连接对象
        @return: None
        """
        connection[2] = wsgi.STATE_CLOSE
        greenio.shutdown_safe(connection[1])
        connection[1].close()
        self.connections.pop(connection[0], None)

    def spawn_handle_request_thread(self) -> None:
        """ 创建专门处理请求的协程

        @return: None
        """
        fun = self.handle_request
        tid = f'{self}.self_handle_request'
        try:
            while not self.stopped:
                try:
                    client, addr = self.wsgi_socket.accept()
                    source_string = f'{addr[0]}:{addr[1]}'
                    target_string = f'{self.listen_host}:{self.listen_port}'
                    logger.debug(f'{source_string} connect to {target_string}')
                    client.settimeout(self.wsgi_server.socket_timeout)
                    args = self.connections[addr] = [addr, client, wsgi.STATE_IDLE]
                    gt = self.container.spawn_splits_thread(fun, args=args, tid=tid)
                    gt.link(self._link_cleanup_connection, self.connections[addr])
                except wsgi.ACCEPT_EXCEPTIONS as accept_exception:
                    if support.get_errno(accept_exception) not in wsgi.ACCEPT_ERRNO:
                        raise accept_exception
                except OSError as e:
                    logger.error(e)
        finally:
            for connection in self.connections.values():
                prev_state = connection[2]
                connection[2] = wsgi.STATE_CLOSE
                (prev_state != wsgi.STATE_CLOSE) and greenio.shutdown_safe(connection[1])
        logger.debug(f'good bey ~')

    def handle_request(self, addr: t.Tuple, client: GreenSocket, state: t.Text) -> None:
        """ 通过server调用app处理

        @param client: 客户端对象
        @param addr: 客户端的地址
        @param state: 套接字状态
        @return: None
        """
        connection = [addr, client, state]
        # 请求最终交由WsgiApp去处理
        self.wsgi_server.process_request(connection)
