#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_core.core.decorator import AsLazyProperty
from service_core.core.endpoint import Endpoint as BaseEndpoint
from service_webserver.constants import DEFAULT_METHODS_THAT_WITH_BODY


class Endpoint(BaseEndpoint):
    """ 通过端点类托管视图 """

    entrypoint_wrapper = None
    entrypoint_options = {}

    @AsLazyProperty
    def router_mapping(self) -> t.Dict[t.Text, t.Callable[..., t.Any]]:
        """ 收集当前端点类下的路由

        主要用于支持基于类的视图

        @return: t.Dict[t.Text, t.Callable[..., t.Any]]
        """
        router_mapping = {}
        super_router_mapping = super(Endpoint, self).router_mapping
        if not self.entrypoint_wrapper: return super_router_mapping
        for method in DEFAULT_METHODS_THAT_WITH_BODY:
            request_method_name = method.upper()
            self.entrypoint_options['methods'] = [request_method_name]
            method = getattr(self.__class__, method.lower(), None)
            if not method: continue
            class_name, method_name = self.__class__.__name__, method.__name__
            method = self.entrypoint_wrapper(**self.entrypoint_options)(method)
            router_mapping.update({f'{class_name}.{method_name}': method})
        return super_router_mapping | router_mapping
