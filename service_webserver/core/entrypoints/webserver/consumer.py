#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t
import werkzeug.exceptions

from eventlet.green import http
from eventlet.event import Event
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from service_green.core.green import json
from eventlet.greenthread import GreenThread
from service_core.core.decorator import AsLazyProperty
from service_webserver.constants import WEBSERVER_CONFIG_KEY
from service_core.exception import gen_exception_description
from service_core.core.service.entrypoint import BaseEntrypoint
from service_webserver.core.context import from_headers_to_context

if t.TYPE_CHECKING:
    from service_core.core.context import WorkerContext

from .producer import ReqProducer


class BaseReqConsumer(BaseEntrypoint):
    """ 通用请求消费者类 """

    name = 'BaseConsumer'

    producer = ReqProducer()

    def __init__(self, raw_url: t.Text, methods: t.Tuple = ('GET',), **options) -> None:
        """ 初始化实例

        @param raw_url: 规则字符
        @param methods: 请求方法
        @param options: 规则选项
        """
        # 相关配置 - 头部映射
        self.headmap = {}

        self.raw_url = raw_url
        self.methods = methods
        self.options = options

        super(BaseReqConsumer, self).__init__()

    def __repr__(self):
        name = super(BaseReqConsumer, self).__repr__()
        return f'{name} - {self.raw_url}'

    @AsLazyProperty
    def rule(self) -> Rule:
        """ 生成规则对象

        @return: Rule
        """
        # 官方推荐并把endpoint的类型限定为字符串! 优化匹配暂且指定为当前entrypoint
        return Rule(self.raw_url, endpoint=self, methods=self.methods, **self.options)

    def setup(self) -> None:
        """ 生命周期 - 载入阶段

        @return: None
        """
        self.producer.reg_extension(self)
        # 主要用于后期异构系统之间通过头部传递特殊信息,例如调用链追踪时涉及的trace信息
        map_headers = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.map_headers', default={})
        self.headmap = map_headers | self.headmap

    def stop(self) -> None:
        """ 生命周期 - 停止阶段

        @return: None
        """
        self.producer.del_extension(self)

    @staticmethod
    def _link_results(gt: GreenThread, event: Event) -> None:
        """ 连接执行结果

        @param gt: 协程对象
        @param event: 事件
        @return: None
        """
        context, excinfo, results = gt.wait()
        event.send((context, excinfo, results))

    def handle_request(self, request) -> t.Tuple:
        """ 处理工作请求

        @param request: 请求对象
        @return: t.Tuple
        """
        event = Event()
        tid = f'{self}.self_handle_request'
        worker_context = from_headers_to_context(dict(request.headers), self.headmap)
        args, kwargs = (request,), request.path_group_dict
        gt = self.container.spawn_worker_thread(self, args, kwargs, worker_context, tid=tid)
        gt.link(self._link_results, event)
        context, excinfo, results = event.wait()
        return context, excinfo, results

    def handle_result(self, context: WorkerContext, results: t.Any) -> t.Any:
        """ 处理正常结果

        @param context: 上下文对象
        @param results: 结果对象
        @return: t.Any
        """
        raise NotImplementedError

    def handle_errors(self, context: WorkerContext, excinfo: t.Tuple) -> t.Any:
        """ 处理异常结果

        @param context: 上下文对象
        @param excinfo: 异常对象
        @return: t.Any
        """
        raise NotImplementedError


class WebReqConsumer(BaseReqConsumer):
    """ WEB请求消费者类 """

    name = 'WebReqConsumer'

    def handle_request(self, request) -> t.Tuple:
        """ 处理工作请求

        @param request: 请求对象
        @return: t.Tuple
        """
        context, results, excinfo = super(WebReqConsumer, self).handle_request(request)
        return (
            self.handle_result(context, results)
            if excinfo is None else
            self.handle_errors(context, excinfo)
        )

    def handle_result(self, context: WorkerContext, results: t.Any) -> t.Any:
        """ 处理正常结果

        @param context: 上下文对象
        @param results: 结果对象
        @return: t.Any
        """
        if isinstance(results, Response):
            return results
        else:
            headers = None
            status = http.HTTPStatus.OK.value
        if not isinstance(results, tuple):
            payload = results
        else:
            if len(results) == 3:
                payload, headers, status = results
            else:
                payload, status = results
        return Response(payload, status=status, headers=headers)

    def handle_errors(self, context: WorkerContext, excinfo: t.Tuple) -> t.Any:
        """ 处理异常结果

        @param context: 上下文对象
        @param excinfo: 异常对象
        @return: t.Any
        """
        exc_type, exc_value, exc_trace = excinfo
        exc_name = exc_type.__name__
        if hasattr(werkzeug.exceptions, exc_name):
            status = getattr(werkzeug.exceptions, exc_name).code
        else:
            status = http.HTTPStatus.INTERNAL_SERVER_ERROR.value
        headers = {'Content-Type': 'text/html; charset=utf-8'}
        data = gen_exception_description(exc_value)
        original = data['original']
        original = f'{original} -' if original else original
        payload = (
            f'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
            f'<title>{status} {exc_type}</title>'
            f'<h1>{data["exc_type"]}</h1>'
            f'<p>from {original}{data["exc_errs"]}</p>'
        )
        return Response(payload, status=status, headers=headers)


class ApiReqConsumer(BaseReqConsumer):
    """ API请求消费者类 """

    name = 'ApiReqConsumer'

    def handle_request(self, request) -> t.Tuple:
        """ 处理工作请求

        @param request: 请求对象
        @return: t.Tuple
        """
        context, results, excinfo = super(ApiReqConsumer, self).handle_request(request)
        return (
            self.handle_result(context, results)
            if excinfo is None else
            self.handle_errors(context, excinfo)
        )

    def handle_result(self, context: WorkerContext, results: t.Any) -> t.Any:
        """ 处理正常结果

        @param context: 上下文对象
        @param results: 结果对象
        @return: t.Any
        """
        status = http.HTTPStatus.OK.value
        headers = {'Content-Type': 'application/json'}
        errs, call_id = None, context.worker_request_id
        payload = json.dumps({'code': status, 'errs': None, 'data': results, 'call_id': call_id})
        return Response(payload, status=status, headers=headers)

    def handle_errors(self, context: WorkerContext, excinfo: t.Tuple) -> t.Any:
        """ 处理异常结果

        @param context: 上下文对象
        @param excinfo: 异常对象
        @return: t.Any
        """
        exc_type, exc_value, exc_trace = excinfo
        exc_name = exc_type.__name__
        if hasattr(werkzeug.exceptions, exc_name):
            status = getattr(werkzeug.exceptions, exc_name).code
        else:
            status = http.HTTPStatus.INTERNAL_SERVER_ERROR.value
        headers = {'Content-Type': 'application/json'}
        data, call_id = None, context.worker_request_id
        errs = gen_exception_description(exc_value)
        payload = json.dumps({'code': status, 'errs': errs, 'data': None, 'call_id': call_id})
        return Response(payload, status=status, headers=headers)
