#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic.fields import ModelField


class Dependant(object):
    """ 依赖注入通用类 """

    def __init__(self, *,
                 name: t.Optional[str] = None,
                 path: t.Optional[str] = None,
                 path_params: t.Optional[t.List[ModelField]] = None,
                 query_params: t.Optional[t.List[ModelField]] = None,
                 header_params: t.Optional[t.List[ModelField]] = None,
                 cookie_params: t.Optional[t.List[ModelField]] = None,
                 body_params: t.Optional[t.List[ModelField]] = None,
                 dependencies: t.Optional[t.List[Dependant]] = None,
                 request_param_name: t.Optional[t.Text] = None,
                 response_param_name: t.Optional[t.Text] = None,
                 use_cache: bool = True
                 ) -> None:
        self.name = name
        self.path = path
        self.use_cache = use_cache
        self.path_params = path_params or []
        self.query_params = query_params or []
        self.header_params = header_params or []
        self.cookie_params = cookie_params or []
        self.body_params = body_params or []
        self.dependencies = dependencies or []
        self.request_param_name = request_param_name
        self.response_param_name = response_param_name
