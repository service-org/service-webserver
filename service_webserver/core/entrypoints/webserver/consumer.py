#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import inspect
import typing as t
import werkzeug.exceptions

from eventlet.green import http
from eventlet.event import Event
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from eventlet.greenthread import GreenThread
from service_core.core.decorator import AsLazyProperty
from service_webserver.core.response import JsonResponse
from service_webserver.core.response import HtmlResponse
from service_webserver.constants import WEBSERVER_CONFIG_KEY
from service_core.exception import gen_exception_description
from service_core.core.service.entrypoint import BaseEntrypoint
from service_webserver.core.openapi3 import create_response_field
from service_webserver.core.context import from_headers_to_context

if t.TYPE_CHECKING:
    from pydantic.fields import ModelField
    from eventlet.green.http import HTTPStatus
    from service_core.core.context import WorkerContext

    # 响应状态
    HttpStatus = t.Optional[t.Union[int, str, HTTPStatus]]

from pydantic.fields import ModelField

from .producer import ReqProducer


class BaseReqConsumer(BaseEntrypoint):
    """ 通用请求消费者类 """

    name = 'BaseReqConsumer'

    producer = ReqProducer()

    def __init__(self,
                 raw_url: t.Text,
                 methods: t.Tuple = ('GET',),
                 tags: t.Optional[t.List] = None,
                 summary: t.Optional[t.Text] = None,
                 status_code: t.Optional[int] = None,
                 description: t.Optional[t.Text] = None,
                 deprecated: t.Optional[bool] = False,
                 operation_id: t.Optional[t.Text] = None,
                 response_class: t.Type[Response] = None,
                 response_description: str = 'Successful Response',
                 response_model: t.Optional[t.Type[t.Any]] = None,
                 include_in_doc: t.Optional[bool] = True,
                 other_response: t.Optional[t.Dict[t.Union[int, str], t.Dict[str, t.Any]]] = None,
                 **options) -> None:
        """ 初始化实例

        @param raw_url: 原始url
        @param methods: 请求方法列表
        @param tags: OpenApi聚合标签列表
        @param summary: OpenApi接口简介
        @param description: OpenApi接口描述
        @param deprecated: OpenApi废弃标识
        @param operation_id: OpenApi操作标识
        @param response_class: 指定特定响应类
        @param response_model: 响应的验证模型
        @param include_in_doc: 是否暴露在文档
        @param options: 其它的相关配置选项
        """
        # 头部映射 - 兼容不同Trace头部
        self.map_headers = {}
        # 路由配置 - 基本的路由相关配置
        methods = {m.upper() for m in methods}
        self.raw_url = raw_url
        self.methods = methods
        self.options = options
        # 响应配置 - 指定响应类构建响应
        self.response_class = response_class
        # Doc配置 - 构建OpenApi的文档
        self._tags = tags
        self._summary = summary
        self._description = description
        self._operation_id = operation_id
        self.deprecated = deprecated
        self.status_code = status_code
        self.other_response = other_response or {}
        self.response_model = response_model
        self.include_in_doc = include_in_doc
        self.response_description = response_description
        self.response_fields = {}
        for status, response in self.other_response.items():
            model = response.get('model')
            name = f'Response_{status}_{self.operation_id}'
            field = create_response_field(name=name, type_=model)
            self.response_fields[status_code] = field
        super(BaseReqConsumer, self).__init__()

    def __repr__(self) -> t.Text:
        name = super(BaseReqConsumer, self).__repr__()
        return f'{name} - {self.raw_url}'

    @AsLazyProperty
    def path(self) -> t.Text:
        """ 获取标准路径

        @return: t.Text
        """
        repl = lambda m: '{' + m.group(1) + '}'
        return re.sub(r'<[^:>]*:([^>]*)>', repl, self.raw_url)

    @AsLazyProperty
    def tags(self) -> t.List:
        """ 获取分组标签

        @return: t.List
        """
        return self._tags or []

    @AsLazyProperty
    def summary(self) -> t.Text:
        """ 获取接口简介

        @return: t.Text
        """
        return self._summary or self.object_name

    @AsLazyProperty
    def description(self) -> t.Text:
        """ 获取接口描述

        @return: t.Text
        """
        if self._description:
            return self._description
        fn_name = self.object_name
        service = self.container.service
        mapping = service.router_mapping
        source = mapping[fn_name].__doc__
        return inspect.getdoc(source)

    @AsLazyProperty
    def operation_id(self) -> t.Text:
        """ 获取操作标识

        @return: t.Text
        """
        name = self.summary.rsplit('.', 1)[-1]
        return re.sub(r'[^0-9a-zA-Z_]', '_', name + self.path)

    @AsLazyProperty
    def response_name(self) -> t.Text:
        """ 生成响应名称

        @return: t.Text
        """
        return f'Response_{self.operation_id}'

    @AsLazyProperty
    def response_field(self) -> ModelField:
        """ 获取响应字段

        @return: t.Optional[ModelField]
        """
        return create_response_field(name=self.response_name, type_=self.response_model)

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
        self.map_headers = map_headers | self.map_headers

    def stop(self) -> None:
        """ 生命周期 - 停止阶段

        @return: None
        """
        self.producer.del_extension(self)

    @staticmethod
    def _gen_response(results: t.Any) -> t.Tuple[t.Any, t.Dict, HttpStatus]:
        """ 生成响应数据

        @param results: 结果对象
        @return: t.Tuple[t.Any, t.Dict, HttpStatus]
        """
        headers = None
        status = http.HTTPStatus.OK.value
        if not isinstance(results, tuple):
            payload = results
        else:
            if len(results) == 3:
                payload, headers, status = results
            else:
                payload, status = results
        return payload, headers, status

    @staticmethod
    def _link_results(gt: GreenThread, event: Event) -> None:
        """ 连接执行结果

        @param gt: 协程对象
        @param event: 事件
        @return: None
        """
        context, results, excinfo = gt.wait()
        event.send((context, results, excinfo))

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
        context, results, excinfo = event.wait()
        return context, results, excinfo

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

    def __init__(self, *args, **kwargs) -> None:
        """ 初始化实例

        @param args  : 位置参数
        @param kwargs: 命名参数
        """
        super(WebReqConsumer, self).__init__(*args, **kwargs)
        self.response_class = self.response_class or HtmlResponse

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
        if isinstance(results, Response): return results
        payload, headers, status = self._gen_response(results)
        response_class = self.response_class or HtmlResponse
        return response_class(payload, status=status, headers=headers)

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
        data = gen_exception_description(exc_value)
        original = data['original']
        original = f'{original} -' if original else original
        payload = (
            f'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
            f'<title>{status} {exc_type}</title>'
            f'<h1>{data["exc_type"]}</h1>'
            f'<p>from {original}{data["exc_errs"]}</p>'
        )
        response_class = self.response_class or HtmlResponse
        return response_class(payload, status=status)


class ApiReqConsumer(BaseReqConsumer):
    """ API请求消费者类 """

    name = 'ApiReqConsumer'

    def __init__(self, *args, **kwargs) -> None:
        """ 初始化实例

        @param args  : 位置参数
        @param kwargs: 命名参数
        """
        super(ApiReqConsumer, self).__init__(*args, **kwargs)
        self.response_class = self.response_class or JsonResponse

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
        if isinstance(results, Response): return results
        payload, headers, status = self._gen_response(results)
        errs, call_id = None, context.worker_request_id
        payload = {'code': status, 'errs': None, 'data': payload, 'call_id': call_id}
        response_class = self.response_class or JsonResponse
        return response_class(payload, status=status)

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
        data, call_id = None, context.worker_request_id
        errs = gen_exception_description(exc_value)
        payload = {'code': status, 'errs': errs, 'data': None, 'call_id': call_id}
        response_class = self.response_class or JsonResponse
        return response_class(payload, status=status)
