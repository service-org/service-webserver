#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import inspect
import typing as t

from functools import partial
from inspect import Parameter
from inspect import Signature
from pydantic.schema import ForwardRef
from pydantic.typing import evaluate_forwardref


def get_typed_annotation(param: Parameter, *, global_ns: t.Dict[t.Text, t.Any]) -> t.Any:
    """ 从注解还原原始的对象

    @param param: 参数对象
    @param global_ns: 命名空间

    @return: t.Any
    """
    annotation = param.annotation
    annotation = ForwardRef(annotation) if isinstance(annotation, str) else annotation
    to_object = partial(evaluate_forwardref, globalns=global_ns, localns=global_ns)
    return to_object(annotation) if isinstance(annotation, ForwardRef) else annotation


def get_typed_signature(call: t.Callable[..., t.Any]) -> Signature:
    """ 从调用构造签名对象

    @param call: 调用对象
    @return: Signature
    """
    signature = inspect.signature(call)
    global_ns = getattr(call, '__globals__', {})
    to_object = partial(get_typed_annotation, global_ns=global_ns)
    parameters = []
    for p in signature.parameters.values():
        parameter = Parameter(p.name, p.kind, default=p.default,
                              annotation=to_object(p))
        parameters.append(parameter)
    return Signature(parameters=parameters)
