#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t


def from_context_to_headers(context: t.Dict, mapping: t.Dict) -> t.Dict:
    """ 从上下文提取并生成头部信息

    @param context: 上下文信息
    @param mapping: 映射转换器
    @return: t.Dict
    """
    headers = {}
    for k, v in context.items():
        k = mapping[k] if k in mapping else k
        headers[k] = v
    return headers


def from_headers_to_context(headers: t.Dict, mapping: t.Dict) -> t.Dict:
    """ 从头部信息提取并生成上下文

    @param headers: 头部信息
    @param mapping: 映射转换器
    @return: t.Dict
    """
    context = {}
    for k, v in headers.items():
        k = mapping[k] if k in mapping else k
        context[k] = v
    return context
