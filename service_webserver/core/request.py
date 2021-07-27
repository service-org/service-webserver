#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

from werkzeug.wrappers.request import Request as BaseRequest


class Request(BaseRequest):
    """ 默认请求基类 """
    pass
