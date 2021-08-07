#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import inspect
import typing as t

from functools import partial
from inspect import Parameter
from pydantic.schema import ForwardRef
from pydantic.typing import evaluate_forwardref


def get_typed_annotation(param: Parameter, *, global_ns: t.Dict[t.Text, t.Any]) -> t.Any:
    """ 从注解获取原始的对象

    @param param: 参数对象
    @param global_ns: 命名空间

    @return: t.Any
    """
    annotation = param.annotation
    annotation = ForwardRef(annotation) if isinstance(annotation, str) else annotation
    # 通过其全局命名空间反射
    to_object = partial(evaluate_forwardref, globalns=global_ns, localns=global_ns)
    return to_object(annotation) if isinstance(annotation, ForwardRef) else annotation


def get_typed_signature(call: t.Callable[..., t.Any]) -> inspect.Signature:
    """ 为调用对象构造签名对象

    @param call: 调用对象
    @return: Signature
    """
    # 解析调用对象的签名信息
    signature = inspect.signature(call)
    # 获取调用对象的全局字典
    global_ns = getattr(call, '__globals__', {})
    # 将参数的注解反射为对象
    to_object = partial(get_typed_annotation, global_ns=global_ns)
    # 重新构建调用对象的签名
    parameters = [inspect.Parameter(name=p.name,
                                    kind=p.kind,
                                    default=p.default,
                                    annotation=to_object(p)
                                    ) for p in signature.parameters.values()]
    return inspect.Signature(parameters=parameters)
