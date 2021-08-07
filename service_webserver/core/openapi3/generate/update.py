#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t


def deep_update_dict(main_dict: t.Dict[t.Any, t.Any], update_dict: t.Dict[t.Any, t.Any]) -> None:
    """ 递归更新字典键值

    @param main_dict: 待更新字典
    @param update_dict: 更新字典
    @return: None
    """
    for key in update_dict:
        if key not in main_dict:
            main_dict[key] = update_dict[key]
        if not isinstance(main_dict[key], dict):
            main_dict[key] = update_dict[key]
        if not isinstance(update_dict[key], dict):
            main_dict[key] = update_dict[key]
        deep_update_dict(main_dict[key], update_dict[key])
