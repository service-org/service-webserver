#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_webserver.core.inspection.models import SecurityBase as SecurityBaseModel


class SecurityBase(object):
    """ 所有安全认证基类

    scheme_name: 认证标识
    model      : 验证模型
    """

    scheme_name: t.Text
    model: SecurityBaseModel


class SecurityScheme(object):
    def __init__(
            self,
            scheme: SecurityBase,
            scopes: t.Optional[t.Sequence[t.Text]] = None
    ) -> None:
        """ 初始化实例

        @param scheme: 安全验证方式
        @param scopes: 权限访问列表
        """
        self.scheme = scheme
        self.scopes = scopes
