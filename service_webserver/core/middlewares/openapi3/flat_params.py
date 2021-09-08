#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic.fields import ModelField
from service_webserver.core.openapi3.generate.depent.models import Dependent
from service_webserver.core.openapi3.generate.depent.helper import get_flat_dependent


def get_flat_params(dependent: Dependent) -> t.List[ModelField]:
    """ 从依赖对象获取扁平化参数

    @param dependent: 依赖对象
    @return: t.List[ModelField]
    """
    flat_dependent = get_flat_dependent(dependent, skip_repeats=True)
    return (
            flat_dependent.path_fields
            + flat_dependent.query_fields
            + flat_dependent.header_fields
            + flat_dependent.cookie_fields
    )
