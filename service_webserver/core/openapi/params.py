#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from enum import Enum
from pydantic.fields import FieldInfo
from pydantic.fields import Undefined


class ParamTypes(Enum):
    """ 参数类型枚举类 """

    query = 'query'
    header = 'header'
    path = 'path'
    cookie = 'cookie'


class Param(FieldInfo):
    """ 通用参数字段类 """

    in_: ParamTypes

    def __init__(self,
                 default: t.Any,
                 *,
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 deprecated: t.Optional[bool] = None,
                 **extra: t.Any
                 ):
        self.deprecated = deprecated
        self.example = example
        self.examples = examples
        super().__init__(
            default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            **extra,
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.default})'


class Path(Param):
    """ 路径参数字段类 """

    in_ = ParamTypes.path

    def __init__(self,
                 default: t.Any,
                 *,
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 deprecated: t.Optional[bool] = None,
                 **extra: t.Any
                 ):
        self.in_ = self.in_
        super().__init__(
            ...,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            deprecated=deprecated,
            example=example,
            examples=examples,
            **extra,
        )


class Query(Param):
    """ 查询参数字段类 """

    in_ = ParamTypes.query

    def __init__(self,
                 default: t.Any,
                 *,
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 deprecated: t.Optional[bool] = None,
                 **extra: t.Any
                 ):
        super().__init__(
            default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            deprecated=deprecated,
            example=example,
            examples=examples,
            **extra,
        )


class Header(Param):
    """ 头部参数字段类 """

    in_ = ParamTypes.header

    def __init__(self,
                 default: t.Any,
                 *,
                 alias: t.Optional[str] = None,
                 convert_underscores: bool = True,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 deprecated: t.Optional[bool] = None,
                 **extra: t.Any
                 ):
        self.convert_underscores = convert_underscores
        super().__init__(
            default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            deprecated=deprecated,
            example=example,
            examples=examples,
            **extra,
        )


class Cookie(Param):
    """ Cookie参数字段类 """

    in_ = ParamTypes.cookie

    def __init__(self,
                 default: t.Any,
                 *,
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 deprecated: t.Optional[bool] = None,
                 **extra: t.Any
                 ):
        super().__init__(
            default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            deprecated=deprecated,
            example=example,
            examples=examples,
            **extra,
        )


class Body(FieldInfo):
    """ Body参数字段类 """

    def __init__(self,
                 default: t.Any,
                 *,
                 embed: bool = False,
                 media_type: str = 'application/json',
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 **extra: t.Any
                 ):
        self.embed = embed
        self.media_type = media_type
        self.example = example
        self.examples = examples
        super().__init__(
            default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            **extra,
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.default})'


class Form(Body):
    """ Form参数字段类 """

    def __init__(self,
                 default: t.Any,
                 *,
                 media_type: str = 'application/x-www-form-urlencoded',
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 **extra: t.Any
                 ):
        super().__init__(
            default,
            embed=True,
            media_type=media_type,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            example=example,
            examples=examples,
            **extra,
        )


class File(Form):
    """ 文件参数字段类 """

    def __init__(self,
                 default: t.Any,
                 *,
                 media_type: str = 'multipart/form-data',
                 alias: t.Optional[str] = None,
                 title: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 gt: t.Optional[float] = None,
                 ge: t.Optional[float] = None,
                 lt: t.Optional[float] = None,
                 le: t.Optional[float] = None,
                 min_length: t.Optional[int] = None,
                 max_length: t.Optional[int] = None,
                 regex: t.Optional[str] = None,
                 example: t.Any = Undefined,
                 examples: t.Optional[t.Dict[str, t.Any]] = None,
                 **extra: t.Any
                 ):
        super().__init__(
            default,
            media_type=media_type,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            regex=regex,
            example=example,
            examples=examples,
            **extra,
        )


class Depends(object):
    """ 通用依赖字段类 """

    def __init__(self,
                 dependency: t.Optional[t.Callable[..., t.Any]] = None,
                 *,
                 use_cache: bool = True):
        self.use_cache = use_cache
        self.dependency = dependency

    def __repr__(self) -> str:
        attr = getattr(self.dependency, '__name__', type(self.dependency).__name__)
        cache = '' if self.use_cache else ', use_cache=False'
        return f'{self.__class__.__name__}({attr}{cache})'


class Security(Depends):
    """ 安全依赖字段类 """

    def __init__(self,
                 dependency: t.Optional[t.Callable[..., t.Any]] = None,
                 *,
                 scopes: t.Optional[t.Sequence[str]] = None,
                 use_cache: bool = True
                 ):
        super().__init__(dependency=dependency, use_cache=use_cache)
        self.scopes = scopes or []
