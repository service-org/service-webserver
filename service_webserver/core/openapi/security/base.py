#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from service_webserver.core.openapi.models import SecurityBase as SecurityBaseModel


class SecurityBase(object):
    schema_name: t.Text
    model: SecurityBaseModel
