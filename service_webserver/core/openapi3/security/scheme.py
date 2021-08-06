#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from .base import BaseSecurity

__all__ = ['SecurityScheme']


class SecurityScheme(object):
    def __init__(self, scheme: BaseSecurity, scopes: t.Optional[t.Sequence[t.Text]] = None) -> None:
        """ 初始化实例

        @param scheme: 安全验证方式
        @param scopes: 权限访问列表
        """
        self.scheme = scheme
        self.scopes = scopes
