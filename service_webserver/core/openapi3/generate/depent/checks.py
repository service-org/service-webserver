#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from logging import getLogger
from pydantic import BaseModel
from pydantic.fields import SHAPE_SET
from pydantic.fields import SHAPE_LIST
from pydantic.fields import SHAPE_TUPLE
from pydantic.fields import ModelField
from pydantic.fields import SHAPE_SEQUENCE
from pydantic.fields import SHAPE_SINGLETON
from pydantic.fields import SHAPE_TUPLE_ELLIPSIS

from . import params

logger = getLogger(__name__)
sequence_types = (list, set, tuple)
sequence_shapes = {SHAPE_SET, SHAPE_LIST, SHAPE_TUPLE, SHAPE_SEQUENCE, SHAPE_TUPLE_ELLIPSIS}
sequence_shapes_mapping = {
    SHAPE_SET: set, SHAPE_LIST: list,
    SHAPE_TUPLE: tuple, SHAPE_SEQUENCE: list,
    SHAPE_TUPLE_ELLIPSIS: list
}


def is_subclass(cls: t.Any, cls_or_tuple: t.Union[t.Type[t.Any], t.Tuple[t.Type[t.Any], ...]]) -> bool:
    """ 是否为对象子类或自身

    @param cls: 任意对象
    @param cls_or_tuple: 类或以类为元素的元组
    @return: bool
    """
    return isinstance(cls, type) and issubclass(cls, cls_or_tuple)


def is_scalar_field(model_field: ModelField) -> bool:
    """ 是否为标量类型字段

    @param model_field: 模型字段
    @return: bool
    """
    field_info = model_field.field_info
    that_types = sequence_types + (dict,)
    is_scalar = (
        # 字段必须是单值类型
        model_field.shape == SHAPE_SINGLETON
        # 注解不是模型类子类
        and not
        is_subclass(model_field.type_, BaseModel)
        # 注解不是序列类子类
        and not
        is_subclass(model_field.type_, that_types)
        # field_info不是body
        and not
        isinstance(field_info, params.Body)
    )
    if not is_scalar:
        return False
    if not model_field.sub_fields:
        return True
    for sub_field in model_field.sub_fields:
        if is_scalar_field(sub_field):
            continue
        return False
    return True


def is_scalar_sequence_field(model_field: ModelField) -> bool:
    """ 是否为标准序列字段

    @param model_field: 模型字段
    @return: bool
    """
    # 通过shape形态判断是否为序列类型字段
    is_sequence_shape = model_field.shape in sequence_shapes
    is_no_model_field = not is_subclass(model_field.type_, BaseModel)
    if is_sequence_shape and is_no_model_field:
        if not model_field.sub_fields:
            return True
        for sub_model_field in model_field.sub_fields:
            if is_scalar_field(sub_model_field):
                continue
            return False
    # 通过type_类型判断是否为序列类型字段
    if is_subclass(model_field.type_, sequence_types):
        return True
    return False
