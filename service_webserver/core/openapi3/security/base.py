#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_webserver.core.openapi3.models import SecurityBase

__all__ = ['BaseSecurity']


class BaseSecurity(object):
    """ 所有安全认证基类

    scheme_name: 认证标识
    model      : 验证模型
    """
    scheme_name: t.Text
    model: SecurityBase
