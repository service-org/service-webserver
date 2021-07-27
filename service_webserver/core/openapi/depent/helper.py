#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import re
import inspect
import typing as t

from pydantic import BaseModel
from pydantic.fields import Required
from pydantic.typing import ForwardRef
from pydantic.fields import SHAPE_SINGLETON
from pydantic.fields import SHAPE_LIST
from pydantic.fields import SHAPE_SET
from pydantic.fields import SHAPE_TUPLE
from pydantic.fields import SHAPE_SEQUENCE
from pydantic.fields import SHAPE_TUPLE_ELLIPSIS
from pydantic.typing import evaluate_forwardref
from service_webserver.core.request import Request
from pydantic.schema import get_annotation_from_field_info

if t.TYPE_CHECKING:
    from inspect import Signature
    from inspect import Parameter
    from pydantic import BaseConfig
    from pydantic.fields import FieldInfo
    from pydantic.fields import ModelField
    from pydantic.fields import UndefinedType
    from pydantic.class_validators import Validator

    from .depent import Dependant

from inspect import Signature
from inspect import Parameter
from pydantic import BaseConfig
from pydantic.fields import FieldInfo

from . import params
from .depent import Dependant

sequence_shapes = {
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_SEQUENCE,
    SHAPE_TUPLE_ELLIPSIS
}

def is_scalar_sequence_field(field: ModelField) -> bool:
    if (field.shape in sequence_shapes) and not issubclass(field.type_, BaseModel):
        if field.sub_fields:
            for sub_field in field.sub_fields:
                if not is_scalar_field(sub_field):
                    return False
        return True
    if issubclass(field.type_, sequence_shapes):
        return True
    return False

def is_scalar_field(field: ModelField) -> bool:
    """ 时候是标准字段

    @param field: 模型字段
    @return: bool
    """
    field_info = field.field_info
    if not(
        field.shape == SHAPE_SINGLETON
        and not issubclass(field.type_, BaseModel)
        and not issubclass(field.type_, (list, set, tuple, dict))
        and not isinstance(field_info, params.Body)
    ):
        return False
    if field.sub_fields:
        if not all(is_scalar_field(f) for f in field.sub_fields):
            return False
    return True


def create_response_field(name: str,
                          type_: t.Type[t.Any],
                          class_validators: t.Optional[t.Dict[str, Validator]] = None,
                          default: t.Optional[t.Any] = None,
                          required: t.Union[bool, UndefinedType] = False,
                          model_config: t.Type[BaseConfig] = BaseConfig,
                          field_info: t.Optional[FieldInfo] = None,
                          alias: t.Optional[str] = None
                          ) -> ModelField:
    class_validators = class_validators or {}
    field_info = field_info or FieldInfo(None)

    return ModelField(name=name,
                      type_=type_,
                      class_validators=class_validators,
                      default=default,
                      required=required,
                      model_config=model_config,
                      field_info=field_info,
                      alias=alias)


def get_param_field(*,
                    param: Parameter,
                    param_name: t.Text,
                    default_field_info: t.Type[params.Param] = params.Param,
                    force_type: t.Optional[params.ParamTypes] = None,
                    ignore_default: bool = False
                    ) -> ModelField:
    default_value = Required
    had_schema = False
    if param.default != param.empty and not ignore_default:
        default_value = param.default
    if isinstance(default_value, FieldInfo):
        had_schema = True
        field_info = default_value
        default_value = field_info.default
        if isinstance(field_info, params.Param) and getattr(field_info, 'in_', None) is None:
            field_info.in_ = default_field_info.in_
        if force_type:
            field_info.in_ = force_type
    else:
        field_info = default_field_info(default_value)
    required = default_value == Required
    annotation = t.Any
    if param.annotation != param.empty:
        annotation = param.annotation
    annotation = get_typed_annotation(annotation, field_info, param_name)
    if not field_info.alias and getattr(field_info, 'convert_underscores', None):
        alias = param.name.replace('_', '-')
    else:
        alias = field_info.alias or param.name
    field = create_response_field(
        name=param.name,
        type_=annotation,
        default=None if required else default_value,
        alias=alias,
        required=required,
        field_info=field_info
    )
    field.required = required
    if not had_schema and not is_scalar_field(field):
        field.field_info = params.Body(field_info.default)
    return field

def add_param_to_field(*, field: ModelField, dependant: Dependant) -> None:
    field_info = t.cast(params.Param, field.field_info)
    if field_info.in_ == params.ParamTypes.path:
        dependant.path_params.append(field)
    if field_info.in_ == params.ParamTypes.query:
        dependant.query_params.append(field)
    if field_info.in_ == params.ParamTypes.header:
        dependant.header_params.append(field)
    if field_info.in_ == params.ParamTypes.cookie:
        dependant.cookie_params.append(field)

def add_non_field_param(*, param: Parameter, dependant: Dependant) -> t.Optional[bool]:
    """ 添加忽略字段的参数

    @param param: 参数对象
    @param dependant: 依赖对象
    @return: t.Optional[bool]:
    """
    # 忽略掉参数为Request的参数,默认首个参数是Request
    if issubclass(param.annotation, Request):
        dependant.request_param_name = param.name
        return True
    return None


def get_param_dependant(*, param: Parameter, path: t.Text) -> Dependant:
    """ 获取参数的子依赖

    @param param: 参数对象
    @param path: 路径
    @return: Dependant
    """
    depends: params.Depends = param.default
    dependency = (param.annotation
                  if not depends.dependency else
                  depends.dependency)
    return get_dependant(call=dependency, path=path, name=param.name)


def get_typed_annotation(param: Parameter, global_ns: t.Dict[t.Text, t.Any]) -> t.Any:
    """ 获取目标函数参数注解

    @param param: 参数对象
    @param global_ns: 全局空间
    @return: t.Any
    """
    annotation = param.annotation
    if isinstance(annotation, str):
        # 将字符串型注解通过全局空间转换为目标对象
        annotation = ForwardRef(annotation)
        annotation = evaluate_forwardref(
            annotation, global_ns, global_ns
        )
    return annotation


def gen_method_signature(call: t.Callable[..., t.Any]) -> Signature:
    """ 生成目标函数签名对象

    @param call: 调用函数
    @return: Signature
    """
    signature = inspect.signature(call)
    # 获取目标函数所在的命名空间全局字典,用于注解反射
    global_ns = getattr(call, '__globals__', {})
    all_param = [Parameter(name=param.name,
                           kind=param.kind,
                           default=param.default,
                           annotation=get_typed_annotation(param, global_ns)
                           ) for param in signature.parameters.values()]
    return Signature(all_param)


def get_path_param_names(path: t.Text) -> t.Set[t.Text]:
    """ 获取路径参数名称集合

    @param path: 请求路径
    @return: t.Set[t.Text]
    """
    return set(re.findall('{(.*?)}', path))


def get_dependant(*, call: t.Callable[..., t.Any], path: t.Text, name: t.Optional[t.Text] = None) -> Dependant:
    """ 递归收集所有依赖对象

    @param call: 调用函数
    @param path: 请求路径
    @param name: 依赖名称
    @return: Dependant
    """
    # 获取所有路径参数名
    path_param_names = get_path_param_names(path)
    # 生成目标函数的签名
    method_signature = gen_method_signature(call)
    # 解析目标函数的参数
    signature_params = method_signature.parameters
    # 创建顶层的依赖对象
    dependant = Dependant(name=name, path=path, call=call)
    for param_name, param in signature_params.items():
        if add_non_field_param(param=param, dependant=dependant):
            continue
        if isinstance(param.default, params.Depends):
            sub_dependant = get_param_dependant(param=param, path=path)
            dependant.dependencies.append(sub_dependant)
            continue
        param_field = get_param_field(
            param=param, default_field_info=params.Query, param_name=param_name
        )
        # 参数名如果在路径参数名中时表示是路径字段
        if param_name in path_param_names:
            if isinstance(param.default, params.Path):
                ignore_default = False
            else:
                ignore_default = True
            param_field = get_param_field(
                param=param,
                param_name=param_name,
                default_field_info=params.Path,
                force_type=params.ParamTypes.path,
                ignore_default=ignore_default
            )
            add_param_to_field(field=param_field, dependant=dependant)
        elif is_scalar_field(field=param_field):
            add_param_to_field(field=param_field, dependant=dependant)
        elif isinstance(param.default, (params.Query, params.Header)) and is_scalar_sequence_field(param_field):
            add_param_to_field(field=param_field, dependant=dependant)
        else:
            dependant.body_params.append(param_field)
        return dependant
