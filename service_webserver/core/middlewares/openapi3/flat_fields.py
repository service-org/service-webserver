#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic.fields import ModelField
from service_webserver.core.entrypoints.webserver.consumer import ReqConsumer

from .flat_params import get_flat_params


def get_flat_fields(routers: t.Sequence[ReqConsumer]) -> t.List[ModelField]:
    """ 从路由中获取所有的字段

    @param routers: 路由列表
    @return: t.List[ModelField]
    """
    body_fields, request_fields, response_fields = [], [], []
    for consumer in routers:
        if not consumer.include_in_doc:
            continue
        if consumer.body_field:
            fields = consumer.body_field
            body_fields.append(fields)
        if consumer.response_field:
            fields = consumer.response_field
            response_fields.append(fields)
        if consumer.other_response_fields:
            fields = consumer.other_response_fields.values()
            response_fields.extend(fields)
        flat_fields = get_flat_params(consumer.dependent)
        request_fields.extend(flat_fields)
    return body_fields + request_fields + response_fields
