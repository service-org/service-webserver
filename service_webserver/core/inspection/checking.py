#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t


def is_subclass(cls: t.Any, cls_or_tuple: t.Union[t.Type[t.Any], t.Tuple[t.Type[t.Any], ...]]) -> bool:
    """ 判断是否为对象子类或类自身

    @param cls: 任意对象
    @param cls_or_tuple: 类或以类为元素的元组
    @return: bool
    """
    return isinstance(cls, type) and issubclass(cls, cls_or_tuple)
