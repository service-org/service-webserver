#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_webserver.core.request import Request

from .base import SecurityBase


class OAuth2(SecurityBase):
    """ OAuth2认证类 """

    def __init__(
            self
    ) -> None:
        """ 初始化实例
        """
        pass

    def __call__(
            self,
            request: Request
    ) -> t.Optional[t.Text]:
        """ 实例可调用

        @param request: 请求对象
        @return: t.Optional[t.Text]
        """
        return
