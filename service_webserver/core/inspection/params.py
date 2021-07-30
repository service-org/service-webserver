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

    path = 'path'
    query = 'query'
    header = 'header'
    cookie = 'cookie'


class Param(FieldInfo):
    """ 通用参数字段类 """

    in_: ParamTypes

    def __init__(
            self,
            default: t.Any,
            *,
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            deprecated: t.Optional[bool] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param alias: 字段别名
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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

    def __repr__(self) -> t.Text:
        return f'{self.__class__.__name__}({self.default})'


class Path(Param):
    """ Path参数字段类 """

    in_ = ParamTypes.path

    def __init__(
            self,
            default: t.Any,
            *,
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            deprecated: t.Optional[bool] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param alias: 字段别名
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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
    """ Query参数字段类 """

    in_ = ParamTypes.query

    def __init__(
            self,
            default: t.Any,
            *,
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            deprecated: t.Optional[bool] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param alias: 字段别名
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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
    """ Header参数字段类 """

    in_ = ParamTypes.header

    def __init__(
            self,
            default: t.Any,
            *,
            alias: t.Optional[t.Text] = None,
            convert_underscores: bool = True,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            deprecated: t.Optional[bool] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param alias: 字段别名
        @param convert_underscores: _转-?
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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

    def __init__(
            self,
            default: t.Any,
            *,
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            deprecated: t.Optional[bool] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param alias: 字段别名
        @param convert_underscores: _转-?
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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

    def __init__(
            self,
            default: t.Any,
            *,
            embed: bool = False,
            media_type: t.Text = 'application/json',
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param embed: {title: default}?
        @param media_type: 媒体类型
        @param alias: 字段别名
        @param convert_underscores: _转-?
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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

    def __repr__(self) -> t.Text:
        return f'{self.__class__.__name__}({self.default})'


class Form(Body):
    """ Form参数字段类 """

    def __init__(
            self,
            default: t.Any,
            *,
            media_type: t.Text = 'application/x-www-form-urlencoded',
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param embed: {title: default}?
        @param media_type: 媒体类型
        @param alias: 字段别名
        @param convert_underscores: _转-?
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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
    """ File参数字段类 """

    def __init__(
            self,
            default: t.Any,
            *,
            media_type: t.Text = 'multipart/form-data',
            alias: t.Optional[t.Text] = None,
            title: t.Optional[t.Text] = None,
            description: t.Optional[t.Text] = None,
            gt: t.Optional[float] = None,
            ge: t.Optional[float] = None,
            lt: t.Optional[float] = None,
            le: t.Optional[float] = None,
            min_length: t.Optional[int] = None,
            max_length: t.Optional[int] = None,
            regex: t.Optional[t.Text] = None,
            example: t.Any = Undefined,
            examples: t.Optional[t.Dict[t.Text, t.Any]] = None,
            **extra: t.Any
    ) -> None:
        """ 初始化实例

        @param default: 字段默认值
        @param embed: {title: default}?
        @param media_type: 媒体类型
        @param alias: 字段别名
        @param convert_underscores: _转-?
        @param title: 原始字段名称
        @param description: 字段描述
        @param gt: 限制大于指定值
        @param ge: 限制大于等于指定值
        @param lt: 限制小于指定值
        @param le: 限制小于等于指定值
        @param min_length: 限制最小长度
        @param max_length: 限制最大长度
        @param regex: 限制正则匹配
        @param example: 符合条件的例子
        @param examples: 其它的符合例子
        @param deprecated: 是否已废弃 ?
        @param extra: 额外的参数
        """
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
    """ 通用依赖注入类 """

    def __init__(
            self,
            dependency: t.Optional[t.Callable[..., t.Any]] = None,
            *,
            use_cache: bool = True
    ) -> None:
        """ 初始化实例

        @param dependency: 可调用对象,通过它分析字段期望值的签名结构
        @param use_cache: 是否使用缓存 ?
        """
        self.use_cache = use_cache
        self.dependency = dependency

    def __repr__(self) -> t.Text:
        attr = getattr(self.dependency, '__name__', type(self.dependency).__name__)
        cache = '' if self.use_cache else ', use_cache=False'
        return f'{self.__class__.__name__}({attr}{cache})'


class Security(Depends):
    """ 安全依赖注入类 """

    def __init__(
            self,
            dependency: t.Optional[t.Callable[..., t.Any]] = None,
            *,
            scopes: t.Optional[t.Sequence[t.Text]] = None,
            use_cache: bool = True
    ) -> None:
        """ 初始化实例

        @param dependency: 可调用对象,通过它分析字段期望值的签名结构
        @param scopes: 权限范围列表
        @param use_cache: 是否使用缓存 ?
        """
        self.scopes = scopes or []
        super().__init__(dependency=dependency, use_cache=use_cache)
