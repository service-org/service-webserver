#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from service_core.core.context import WorkerContext

from eventlet.event import Event
from werkzeug.routing import Rule
from eventlet.greenthread import GreenThread
from service_core.core.decorator import AsLazyProperty
from service_core.core.service.entrypoint import BaseEntrypoint

if t.TYPE_CHECKING:
    pass

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
        self.raw_url = raw_url
        self.methods = methods
        self.options = options
        super(BaseReqConsumer, self).__init__()

    @AsLazyProperty
    def rule(self) -> Rule:
        """ 生成规则对象

        @return: Rule
        """
        return Rule(self.raw_url, methods=self.methods, **self.options)

    def setup(self) -> None:
        """ 生命周期 - 载入阶段

        @return: None
        """
        self.producer.reg_extension(self)

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
        pass

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
        pass

    def handle_errors(self, context: WorkerContext, excinfo: t.Tuple) -> t.Any:
        """ 处理异常结果

        @param context: 上下文对象
        @param excinfo: 异常对象
        @return: t.Any
        """
        pass


class ApiReqConsumer(BaseReqConsumer):
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
        pass

    def handle_errors(self, context: WorkerContext, excinfo: t.Tuple) -> t.Any:
        """ 处理异常结果

        @param context: 上下文对象
        @param excinfo: 异常对象
        @return: t.Any
        """
        pass
