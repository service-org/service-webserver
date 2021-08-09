#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

# WEB服务配置
WEBSERVER_CONFIG_KEY = 'WEBSERVER'
DEFAULT_WEBSERVER_MAX_CONNECTIONS = 65535
DEFAULT_WEBSERVER_HEADERS_MAPPING = {

}

# DOC服务配置
DEFAULT_DEFINITIONS_REF_PREFIX = '#/components/schemas/'
DEFAULT_CODE_THAT_WITH_NO_BODY = {100, 102, 102, 103, 204, 304}
DEFAULT_METHODS_THAT_WITH_BODY = {'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'PATCH'}
DEFAULT_ALL_STATUS_CODE_RANGES = {
    '1XX': 'Information',
    '2XX': 'Success',
    '3XX': 'Redirection',
    '4XX': 'Client Error',
    '5XX': 'Server Error',
    'DEFAULT': 'Default Response',
}
DEFAULT_METHODS_THAT_SUPPORTED = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'CONNECT', 'HEAD', 'OPTIONS', 'TRACE']
