#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

__all__ = ['get_swagger_payload']


def get_swagger_payload():
    """ 获取swagger载体 """
    return '/swagger'


import re

print(re.sub(r'<[^:>]*:([^>]*)>', lambda m: '{' + m.group(1) + '}', '/object/<uuid:identifier>/<uuid:xxxx>'))
