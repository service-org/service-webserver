#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_core.core.endpoint import Endpoint as BaseEndpoint
from service_webserver.constants import DEFAULT_METHODS_THAT_WITH_BODY


class Endpoint(BaseEndpoint):
    """ 通过端点类托管视图 """

    entrypoint_wrapper = None
    entrypoint_options = {}

    def router_mapping(self) -> t.Dict[t.Text, t.Callable[..., t.Any]]:
        """ 收集当前端点实例下路由

        主要用于支持基于类的视图

        @return: t.Dict[t.Text, t.Callable[..., t.Any]]
        """
        router_mapping = {}
        super_router_mapping = super(Endpoint, self).router_mapping()
        if not self.entrypoint_wrapper: return super_router_mapping
        class_name = self.__class__.__name__
        for method in DEFAULT_METHODS_THAT_WITH_BODY:
            method_name = method.lower()
            # 将当前类下的entrypoint注入到对应类方法的entrypoints属性中
            cls_method = getattr(self.__class__, method_name, None)
            if not cls_method: continue
            self.entrypoint_wrapper(methods=[method.upper()], **self.entrypoint_options)(cls_method)
            ins_method = getattr(self, method.lower())
            module_name = ins_method.__module__.rsplit('.', 1)[-1]
            # 最终注入到路由映射表中的应该是方法的点分路径和当前实例的方法
            router_mapping.update({f'{module_name}.{class_name}.{method_name}': ins_method})
        return super_router_mapping | router_mapping
