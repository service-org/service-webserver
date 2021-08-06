#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t


class SecurityScopes(object):
    """ 权限范围基类 """

    def __init__(self, scopes: t.Optional[t.List[t.Text]] = None):
        """ 初始化实例

        @param scopes: 权限范围列表
        """
        self.scopes = scopes or []

    def __repr__(self):
        return ' '.join(self.scopes)
