#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from pydantic import BaseConfig
    from pydantic.fields import FieldInfo
    from pydantic.fields import ModelField
    from pydantic.fields import UndefinedType
    from pydantic.class_validators import Validator

from pydantic import BaseConfig

def get_dependant(
    *,
    path: str,
    call: t.Callable[..., t.Any],
    name: t.Optional[str] = None,
    security_scopes: t.Optional[t.List[str]] = None,
    use_cache: bool = True,
) -> Dependant:
    pass


def create_response_field(name: str,
                          type_: t.Type[t.Any],
                          class_validators: t.Optional[t.Dict[str, Validator]] = None,
                          default: t.Optional[t.Any] = None,
                          required: t.Union[bool, UndefinedType] = False,
                          model_config: t.Type[BaseConfig] = BaseConfig,
                          field_info: t.Optional[FieldInfo] = None,
                          alias: t.Optional[str] = None
                          ) -> ModelField:
    """ 创建一个响应字段

    @param name: 字段名称
    @param type_: 字段类型
    @param class_validators: 字段验证
    @param default: 默认值
    @param required: 是否必须
    @param model_config: 模型配置
    @param field_info: 字段详情
    @param alias: 字段别名
    @return:
    """
    class_validators = class_validators or {}
    field_info = field_info or FieldInfo(None)

    return ModelField(
        name=name,
        type_=type_,
        class_validators=class_validators,
        default=default,
        required=required,
        model_config=model_config,
        field_info=field_info,
        alias=alias,
    )
