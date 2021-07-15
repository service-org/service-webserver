#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

from service_core.exception import Error


class BadRequest(Error):
    """ 400异常请求 """
    pass
