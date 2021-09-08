#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from enum import Enum
from pydantic import BaseModel
from pydantic.schema import get_flat_models_from_fields
from service_webserver.core.entrypoints.webserver.consumer import ReqConsumer

from .flat_fields import get_flat_fields


def get_flat_models(routers: t.Sequence[ReqConsumer]) -> t.Set[t.Union[t.Type[BaseModel], t.Type[Enum]]]:
    """ 从路由中获取所有的模型

    @param routers: 路由列表
    @return: t.Set[t.Union[t.Type[BaseModel], t.Type[enum.Enum]]]
    """
    flat_fields = get_flat_fields(routers)
    return get_flat_models_from_fields(flat_fields, known_models=set())
