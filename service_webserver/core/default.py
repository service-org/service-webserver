#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from http import HTTPStatus
from pydantic import BaseModel
from pydantic.fields import Field

HTTP100 = HTTPStatus.CONTINUE.value
HTTP200 = HTTPStatus.OK.value
HTTP511 = HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED.value


class DefaultResponseModel(BaseModel):
    """ 默认响应模型 """

    code: int = Field(default=HTTP200, description='响应状态', ge=HTTP100, le=HTTP511)
    errs: t.Optional[t.Dict] = Field(description='异常详情')
    data: t.Optional[t.Any] = Field(description='响应结果')
    call_id: t.Text = Field(description='调用链ID')
