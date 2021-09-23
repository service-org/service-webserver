#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import sys
import enum
import eventlet
import typing as t
import werkzeug.exceptions

from http import HTTPStatus
from logging import getLogger
from eventlet.event import Event
from werkzeug.routing import Rule
from pydantic.fields import ModelField
from werkzeug.wrappers import Response
from eventlet.greenthread import GreenThread
from service_core.core.context import WorkerContext
from service_core.core.decorator import AsLazyProperty
from service_webserver.core.response import JsonResponse
from service_webserver.core.response import HtmlResponse
from service_core.core.storage import green_thread_local
from service_core.core.service.entrypoint import Entrypoint
from service_webserver.constants import WEBSERVER_CONFIG_KEY
from service_core.exchelper import gen_exception_description
from service_webserver.core.default import DefaultResponseModel
from service_webserver.core.convert import from_headers_to_context
from service_webserver.core.openapi3.generate.depent.models import Dependent
from service_webserver.core.openapi3.generate.depent.helper import get_dependent
from service_webserver.core.openapi3.generate.depent.field import gen_model_field
from service_webserver.core.openapi3.generate.depent.helper import get_body_field

from .producer import ReqProducer

logger = getLogger(__name__)
# 响应状态
HttpStatus = t.Optional[t.Union[int, str, HTTPStatus]]


class ReqConsumer(Entrypoint):
    """ 通用请求消费者类 """

    name = 'ReqConsumer'

    producer = ReqProducer()

    def __init__(
            self,
            raw_url: t.Text,
            methods: t.Tuple = ('GET',),
            tags: t.Optional[t.List] = None,
            summary: t.Optional[t.Text] = None,
            status_code: t.Optional[int] = None,
            description: t.Optional[t.Text] = None,
            deprecated: t.Optional[bool] = False,
            operation_id: t.Optional[t.Text] = None,
            response_class: t.Type[Response] = None,
            response_description: t.Text = 'Successful Response',
            response_model: t.Optional[t.Type[t.Any]] = DefaultResponseModel,
            include_in_doc: t.Optional[bool] = True,
            other_response: t.Optional[t.Dict[t.Union[int, t.Text], t.Dict[t.Text, t.Any]]] = None,
            rule_options: t.Optional[t.Dict[t.Text, t.Any]] = None,
            **kwargs
    ) -> None:
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
        @param rule_options: 路由其它配置选项
        @param kwargs: 其它的相关配置选项
        """
        # 用于兼容不同的追踪协议头部
        self.map_headers = {}
        self.raw_url = raw_url
        self._methods = methods
        self.tags = tags or []
        self._summary = summary
        # werkzeug.routing.Rule
        self.rule_options = rule_options or {}
        self.deprecated = deprecated
        self._operation_id = operation_id
        self._description = description
        self.other_response_fields = {}
        self._status_code = status_code
        self.response_model = response_model
        self.response_class = response_class
        self.other_response = other_response or {}
        # other_response响应字段
        self._setup_other_response_fields()
        self.include_in_doc = include_in_doc
        self.response_description = response_description
        super(ReqConsumer, self).__init__(**kwargs)

    def __repr__(self) -> t.Text:
        name = super(ReqConsumer, self).__repr__()
        return f'{name} - {self.raw_url}'

    @AsLazyProperty
    def path(self) -> t.Text:
        """ 规范路径 """
        repl = lambda m: '{' + m.group(1) + '}'
        return re.sub(r'<[^:>]*:([^>]*)>', repl, self.raw_url)

    @AsLazyProperty
    def methods(self) -> t.Set:
        """ 请求方法 """
        return {m.upper() for m in self._methods}

    @AsLazyProperty
    def summary(self) -> t.Text:
        """ 接口简述 """
        title = self._summary or self.object_name
        desc = self.description.split(maxsplit=1)[0].strip() if self.description else ''
        return f'{title} - {desc}' if desc else title

    @AsLazyProperty
    def status_code(self) -> int:
        """ 响应代码 """
        return int(self.status_code) if isinstance(self._status_code, enum.IntEnum) else self._status_code

    @AsLazyProperty
    def operation_id(self) -> t.Text:
        """ 操作标识 """
        op_id = re.sub(r'[^0-9a-zA-Z_]', '_', self.path)
        return op_id.replace('__', '_').strip('_')

    @AsLazyProperty
    def response_name(self) -> t.Text:
        """ 响应名称 """
        return f'Response_{self.operation_id}'

    @AsLazyProperty
    def description(self) -> t.Text:
        """ 接口描述 """
        return (self._description or self.endpoint.__doc__ or '').strip()

    @AsLazyProperty
    def endpoint(self) -> t.Callable[..., t.Any]:
        """ 视图函数 """
        return self.container.service.router_mapping[self.object_name]

    @AsLazyProperty
    def dependent(self) -> Dependent:
        """ 依赖对象 """
        return get_dependent(path=self.path, call=self.endpoint, name=self.summary)

    @AsLazyProperty
    def body_field(self) -> t.Optional[ModelField]:
        """ body字段 """
        return get_body_field(dependent=self.dependent, name=self.operation_id)

    @AsLazyProperty
    def response_field(self) -> t.Optional[ModelField]:
        """ 响应字段 """
        return gen_model_field(name=self.response_name, type_=self.response_model) if self.response_model else None

    @AsLazyProperty
    def rule(self) -> Rule:
        """ 生成规则对象

        @return: Rule
        """
        # 官方推荐并把endpoint的类型限定为字符串! 优化匹配暂且指定为当前entrypoint
        return Rule(self.raw_url, endpoint=self, methods=self.methods, **self.rule_options)  # type: ignore

    def setup(self) -> None:
        """ 生命周期 - 载入阶段

        @return: None
        """
        self.producer.reg_extension(self)
        # 主要用于后期异构系统之间通过头部传递特殊信息,例如调用链追踪时涉及的trace信息
        map_headers = self.container.config.get(f'{WEBSERVER_CONFIG_KEY}.map_headers', default={})
        # 防止YAML中声明值为None
        self.map_headers = (map_headers or {}) | self.map_headers

    def stop(self) -> None:
        """ 生命周期 - 停止阶段

        @return: None
        """
        self.producer.del_extension(self)

    def _setup_other_response_fields(self) -> None:
        """ 载入响应字段

        @return: None
        """
        for code, response in self.other_response.items():
            is_dict_response = isinstance(response, dict)
            if not is_dict_response:
                logger.error(f"{code}'s response must was dict")
                continue
            response_model = response.get('model')
            if not response_model:
                logger.error(f"{code}'s response must has model")
                continue
            response_name = f'Response_{code}_{self.operation_id}'
            response_field = gen_model_field(
                name=response_name, type_=response_model
            )
            self.other_response_fields[code] = response_field

    @staticmethod
    def _gen_response(results: t.Any) -> t.Tuple[t.Any, t.Dict, HttpStatus]:
        """ 生成响应数据

        @param results: 结果对象
        @return: t.Tuple[t.Any, t.Dict, HttpStatus]
        """
        headers = None
        status = HTTPStatus.OK.value
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
        # fix: 此协程异常会导致收不到event最终内存溢出!
        try:
            context, results, excinfo = gt.wait()
        except BaseException:
            results, excinfo = None, sys.exc_info()
            context = eventlet.getcurrent().context
        event.send((context, results, excinfo))

    def handle_request(self, request) -> t.Tuple:
        """ 处理工作请求

        @param request: 请求对象
        @return: t.Tuple
        """
        event = Event()
        tid = f'{self}.self_handle_request'
        request_header = dict(request.headers)
        worker_context = from_headers_to_context(request_header, self.map_headers)
        args, kwargs = (request,), request.path_group_dict
        gt = self.container.spawn_worker_thread(self, args, kwargs, worker_context, tid=tid)
        gt.link(self._link_results, event)
        # 注意: 此协程异常会导致收不到event最终内存溢出!
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


class WebReqConsumer(ReqConsumer):
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
        # 如果存在定义的同名异常类则使用对应的异常类的code值作为响应码
        if hasattr(werkzeug.exceptions, exc_name):
            status = getattr(werkzeug.exceptions, exc_name).code
        else:
            status = HTTPStatus.INTERNAL_SERVER_ERROR.value
        data = gen_exception_description(exc_value)
        original = data['original']
        original = f'{original} -' if original else original
        payload = (
            f'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
            f'<title>{status} {exc_type}</title>'
            f'<h1>{data["exc_type"]}</h1>'
            f'<p>{original}{data["exc_errs"]}</p>'
        )
        response_class = self.response_class or HtmlResponse
        return response_class(payload, status=status)


class ApiReqConsumer(ReqConsumer):
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
        # 如果存在定义的同名异常类则使用对应的异常类的code值作为响应码
        if hasattr(werkzeug.exceptions, exc_name):
            status = getattr(werkzeug.exceptions, exc_name).code
        else:
            status = HTTPStatus.INTERNAL_SERVER_ERROR.value
        data, call_id = None, context.worker_request_id
        errs = gen_exception_description(exc_value)
        payload = {'code': status, 'errs': errs, 'data': None, 'call_id': call_id}
        response_class = self.response_class or JsonResponse
        return response_class(payload, status=status)
