#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from logging import getLogger

logger = getLogger(__name__)


def is_subclass(obj: t.Any, cls_or_tuple: t.Union[t.Type[t.Any], t.Tuple[t.Type[t.Any], ...]]) -> bool:
    """ 是否为对象子类 ?

    @param obj: 任意对象
    @param cls_or_tuple: 子类元组
    @return: bool
    """
    return isinstance(obj, type) and issubclass(obj, cls_or_tuple)
