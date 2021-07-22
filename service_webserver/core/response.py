#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import html
import typing as t

from eventlet.green import http
from werkzeug.urls import iri_to_uri
from werkzeug.wsgi import FileWrapper
from service_green.core.green import json
from werkzeug.utils import get_content_type

if t.TYPE_CHECKING:
    from eventlet.green.http import HTTPStatus
    from werkzeug.wrappers.response import Response

    # 响应内容
    HttpResponse = t.Optional[t.Union[t.Iterable[bytes], bytes, t.Iterable[str], str]]
    # 响应状态
    HttpStatus = t.Optional[t.Union[int, str, HTTPStatus]]
    # 字典头部
    HTTPDictHeaders = t.Mapping[str, t.Union[str, int, t.Iterable[t.Union[str, int]]]]
    # 元组头部
    HTTPIterHeaders = t.Iterable[t.Tuple[str, t.Union[str, int]]]
    # 响应头部
    HttpHeaders = t.Optional[t.Union[HTTPDictHeaders, HTTPIterHeaders]]

from werkzeug.wrappers.response import Response

__all__ = ['HtmlResponse', 'JsonResponse', 'RedirectResponse', 'PlainTextResponse', 'StreamResponse', 'FileResponse']


class BaseResponse(Response):
    """ 默认响应基类 """

    json_module = json
    mimetype = 'text/plain'

    def __init__(self, response: HttpResponse = None, status: HTTPStatus = None, headers: HTTPDictHeaders = None,
                 mimetype: t.Optional[str] = None, content_type: t.Optional[str] = None,
                 direct_passthrough: bool = False
                 ) -> None:
        """ 初始化实例

        @param response: 响应内容
        @param status  : 响应状态
        @param headers : 头部信息
        @param mimetype: 内容类型
        @param content_type: 响应类型
        @param direct_passthrough: 是否以流式直传?
        """
        headers = headers or {}
        headers['Content-Type'] = get_content_type(self.mimetype, self.charset)
        super(BaseResponse, self).__init__(response, status, headers, mimetype, content_type, direct_passthrough)


class HtmlResponse(BaseResponse):
    """ 网页格式响应类 """

    mimetype = 'text/html'


class JsonResponse(BaseResponse):
    """ JSON格式响应类 """
    mimetype = 'application/json'

    def __init__(self, response: HttpResponse = None, status: HTTPStatus = None, headers: HTTPDictHeaders = None,
                 mimetype: t.Optional[str] = None, content_type: t.Optional[str] = None,
                 direct_passthrough: bool = False
                 ) -> None:
        """ 初始化实例

        @param response: 响应内容
        @param status  : 响应状态
        @param headers : 头部信息
        @param mimetype: 内容类型
        @param content_type: 响应类型
        @param direct_passthrough: 是否以流式直传?
        """
        response = json.dumps(response, ident=None)
        super(BaseResponse, self).__init__(response, status, headers, mimetype, content_type, direct_passthrough)


class PlainTextResponse(BaseResponse):
    """ 文本格式响应类 """

    mimetype = 'text/plain'


class RedirectResponse(BaseResponse):
    """ 跳转格式响应类 """

    mimetype = 'text/html'

    def __init__(self, location: t.Text, response: HttpResponse = None, status: HTTPStatus = None,
                 headers: HTTPDictHeaders = None, mimetype: t.Optional[str] = None,
                 content_type: t.Optional[str] = None,
                 direct_passthrough: bool = False
                 ) -> None:
        """ 初始化实例

        doc: werkzeug.utils.redirect

        @param location: 跳转地址
        @param response: 响应内容
        @param status  : 响应状态
        @param headers : 头部信息
        @param mimetype: 内容类型
        @param content_type: 响应类型
        @param direct_passthrough: 是否以流式直传?
        """
        status = http.HTTPStatus.FOUND.value
        if isinstance(location, str):
            # Safe conversion is necessary here as we might redirect
            # to a broken URI scheme (for instance itms-services).
            location = iri_to_uri(location, safe_conversion=True)
        headers = headers or {}
        headers['Location'] = location
        display_location = html.escape(location)
        response = (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            "<title>Redirecting...</title>\n"
            "<h1>Redirecting...</h1>\n"
            "<p>You should be redirected automatically to target URL: "
            f'<a href="{html.escape(location)}">{display_location}</a>. If'
            " not click the link."
        )
        super(RedirectResponse, self).__init__(response, status, headers, mimetype, content_type, direct_passthrough)


class StreamResponse(BaseResponse):
    """ 流式格式响应类 """

    buffer_size = 8192
    mimetype = 'application/octet-stream'

    def __init__(self, response: HttpResponse = None, status: HTTPStatus = None, headers: HTTPDictHeaders = None,
                 mimetype: t.Optional[str] = None, content_type: t.Optional[str] = None,
                 direct_passthrough: bool = False
                 ) -> None:
        """ 初始化实例

        doc: werkzeug.utils.wrap_file

        @param response: 响应内容
        @param status  : 响应状态
        @param headers : 头部信息
        @param mimetype: 内容类型
        @param content_type: 响应类型
        @param direct_passthrough: 是否以流式直传?
        """
        direct_passthrough = True
        response = FileWrapper(response, buffer_size=self.buffer_size)  # type: ignore
        super(StreamResponse, self).__init__(response, status, headers, mimetype, content_type, direct_passthrough)


class FileResponse(BaseResponse):
    """ 文件格式响应 """

    mimetype = 'application/octet-stream'

    def __init__(self, response: HttpResponse = None, status: HTTPStatus = None, headers: HTTPDictHeaders = None,
                 mimetype: t.Optional[str] = None, content_type: t.Optional[str] = None,
                 direct_passthrough: bool = False
                 ) -> None:
        """ 初始化实例

        doc: werkzeug.utils.wrap_file

        @param response: 响应内容
        @param status  : 响应状态
        @param headers : 头部信息
        @param mimetype: 内容类型
        @param content_type: 响应类型
        @param direct_passthrough: 是否以流式直传?
        """
        direct_passthrough = True
        response = FileWrapper(response, buffer_size=self.buffer_size)  # type: ignore
        super(FileResponse, self).__init__(response, status, headers, mimetype, content_type, direct_passthrough)