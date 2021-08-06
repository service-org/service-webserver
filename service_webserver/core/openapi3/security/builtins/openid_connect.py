#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_webserver.core.request import Request
from service_webserver.core.openapi3.security.base import BaseSecurity


class OpenIdConnect(BaseSecurity):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """ 初始化实例

        @param args  : 位置参数
        @param kwargs: 命名参数
        """
        pass

    def __call__(self, request: Request) -> t.Optional[t.Text]:
        """ 对象可调用

        @param request: 请求对象
        @return: t.Optional[t.Text]
        """
        return
