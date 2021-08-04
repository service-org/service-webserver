#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from pydantic.fields import ModelField

from .security.base import SecurityScheme


class Dependant(object):
    """ 通用依赖注入类 """

    def __init__(
            self,
            *,
            use_cache: bool = True,
            name: t.Optional[t.Text] = None,
            path: t.Optional[t.Text] = None,
            call: t.Optional[t.Callable[..., t.Any]] = None,
            path_fields: t.Optional[t.List[ModelField]] = None,
            query_fields: t.Optional[t.List[ModelField]] = None,
            header_fields: t.Optional[t.List[ModelField]] = None,
            cookie_fields: t.Optional[t.List[ModelField]] = None,
            body_fields: t.Optional[t.List[ModelField]] = None,
            dependencies: t.Optional[t.List[Dependant]] = None,
            request_field_name: t.Optional[t.Text] = None,
            service_field_name: t.Optional[t.Text] = None,
            response_field_name: t.Optional[t.Text] = None,
            security_scopes: t.Optional[t.List[t.Text]] = None,
            security_scopes_field_name: t.Optional[t.Text] = None,
            security_schemes: t.Optional[t.List[SecurityScheme]] = None,
    ) -> None:
        """ 初始化实例

        @param use_cache: 使用缓存?
        @param name: 依赖名称
        @param path: 请求路径
        @param call: 调用对象
        @param path_fields: path参数字段列表
        @param query_fields: query参数字段列表
        @param header_fields: header参数字段列表
        @param cookie_fields: cookie参数字段列表
        @param body_fields: body参数字段列表
        @param dependencies: 下级依赖对象列表
        @param request_field_name: request字段名
        @param service_field_name: service字段名
        @param response_field_name: response字段名
        @param security_scopes: 安全范围列表
        @param security_scopes_field_name: 安全范围字段名
        @param security_schemes: 安全认证方式列表
        """
        self.name = name
        self.path = path
        self.call = call
        self.use_cache = use_cache
        self.path_fields = path_fields or []
        self.query_fields = query_fields or []
        self.header_fields = header_fields or []
        self.cookie_fields = cookie_fields or []
        self.body_fields = body_fields or []
        self.dependencies = dependencies or []
        self.request_field_name = request_field_name
        self.service_field_name = service_field_name
        self.response_field_name = response_field_name
        self.security_scopes = security_scopes
        self.security_schemes = security_schemes or []
        self.security_scopes_field_name = security_scopes_field_name
