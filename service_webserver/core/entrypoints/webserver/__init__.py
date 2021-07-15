#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

from .consumer import WebReqConsumer
from .consumer import ApiReqConsumer

web = WebReqConsumer.as_decorators
api = ApiReqConsumer.as_decorators
