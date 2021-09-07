#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic import BaseConfig
from pydantic.fields import Undefined
from pydantic.fields import FieldInfo
from pydantic.fields import ModelField
from pydantic.typing import NoArgAnyCallable
from pydantic.class_validators import Validator

if t.TYPE_CHECKING:
    from pydantic.fields import BoolUndefined


def gen_model_field(
        *,
        name: t.Text,
        type_: t.Type[t.Any],
        class_validators: t.Optional[t.Dict[t.Text, Validator]] = None,
        model_config: t.Type[BaseConfig] = None,
        default: t.Any = None,
        default_factory: t.Optional[NoArgAnyCallable] = None,
        required: BoolUndefined = Undefined,
        alias: str = None,
        field_info: t.Optional[FieldInfo] = None,
) -> ModelField:
    """ 生成模型字段

    @param name: 字段名称
    @param type_: 验证模型
    @param class_validators: 加验证器
    @param model_config: 模型配置
    @param default: 默认值
    @param default_factory: 默认值函数
    @param required: 必要字段?
    @param alias: 字段别名
    @param field_info: 额外信息辅助验证
    @return: ModelField
    """
    class_validators = class_validators or {}
    model_config = model_config or BaseConfig
    field_info = field_info or FieldInfo(None)
    return ModelField(
        name=name,
        type_=type_,
        class_validators=class_validators,
        model_config=model_config,
        default=default,
        default_factory=default_factory,
        required=required,
        alias=alias,
        field_info=field_info
    )
