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
from werkzeug.wrappers.request import Request
from pydantic.fields import SHAPE_TUPLE_ELLIPSIS
from pydantic.typing import evaluate_forwardref
from service_core.core.service.base import BaseService
from pydantic.schema import get_annotation_from_field_info

if t.TYPE_CHECKING:
    from inspect import Signature
    from inspect import Parameter
    from pydantic import BaseConfig
    from pydantic.fields import FieldInfo
    from pydantic.fields import ModelField
    from pydantic.fields import UndefinedType
    from pydantic.class_validators import Validator

    from .models import Dependant

from inspect import Signature
from inspect import Parameter
from pydantic import BaseConfig
from pydantic.fields import FieldInfo
from pydantic.fields import ModelField

from service_webserver.core.openapi import params

from .models import Dependant

sequence_shapes = {
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_SEQUENCE,
    SHAPE_TUPLE_ELLIPSIS
}

is_subclass = lambda t, ts: isinstance(t, type) and issubclass(t, ts)

def is_scalar_sequence_field(field: ModelField) -> bool:
    if (field.shape in sequence_shapes) and not is_subclass(field.type_, BaseModel):
        if field.sub_fields:
            for sub_field in field.sub_fields:
                if not is_scalar_field(sub_field):
                    return False
        return True
    if is_subclass(field.type_, sequence_shapes):
        return True
    return False


def is_scalar_field(field: ModelField) -> bool:
    """ 是否是标准字段

    @param field: 模型字段
    @return: bool
    """
    field_info = field.field_info
    if not (
            field.shape == SHAPE_SINGLETON
            and not is_subclass(field.type_, BaseModel)
            and not is_subclass(field.type_, (list, set, tuple, dict))
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
    # 字段默认值是必须字段, 例如 short: bool
    default_value = Required
    had_schema = False
    # 默认值不为空并且不忽略默认值,例如 short: bool = True
    if param.default != param.empty and not ignore_default:
        # 此时默认值就是参数的默认值
        default_value = param.default
    # 如果是pydantic.fields下的字段的话, 例如short: bool = Field(...)
    if isinstance(default_value, FieldInfo):
        had_schema = True
        field_info = default_value
        # 将默认值设置为pydantic.fields下的字段的默认值
        default_value = field_info.default
        # 如果field_info是自定义的Body File Form的field_info子类的话但不存在in_属性
        if isinstance(field_info, params.Param) and getattr(field_info, 'in_', None) is None:
            field_info.in_ = default_field_info.in_
        if force_type:
            field_info.in_ = force_type
    else:
        # 当不是field_info实例时包装成默认field_info
        field_info = default_field_info(default_value)
    # 其实只要是不写默认值或默认值不是FieldInfo实例的话其实默认就是必填字段
    required = default_value == Required
    # 开始分析注解
    annotation = t.Any
    # 当注解不为空时
    if param.annotation != param.empty:
        annotation = param.annotation
    # 从field_info反射获取annotation对象
    annotation = get_annotation_from_field_info(annotation, field_info, param_name)
    # 根据是否需要转换下划线来生成alias别名
    if not field_info.alias and getattr(field_info, 'convert_underscores', None):
        alias = param.name.replace('_', '-')
    else:
        alias = field_info.alias or param.name
    # 创建一个模型字段
    field = create_response_field(
        name=param.name,
        type_=annotation,
        default=None if required else default_value,
        alias=alias,
        required=required,
        field_info=field_info
    )
    # 设置是否必须字段
    field.required = required
    # 如果不是FieldInfo的实例并且也不是通用字段的话就作为请求体字段
    if not had_schema and not is_scalar_field(field):
        # 包装成为请求体字段
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
    # 忽略掉参数为self的参数
    # if is_subclass(param.annotation, BaseService):
    #     return True
    # 忽略掉参数为Request的参数
    if is_subclass(param.annotation, Request):
        dependant.request_param_name = param.name
        return True
    return None


def get_param_dependant(*, param: Parameter, path: t.Text) -> Dependant:
    """ 获取参数的子依赖

    @param param: 参数对象
    @param path: 路径
    @return: Dependant
    """
    # 默认值就是依赖注入对象
    depends = param.default
    # dependency是一个可调用对象,如果存在则将其作为get_dependant的call参数递归注入否则将反射后的annotation作为call参数
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
    # 生成目标函数的签名
    method_signature = gen_method_signature(call)
    # 解析目标函数的参数
    signature_params = method_signature.parameters
    # 创建顶层的依赖对象
    dependant = Dependant(name=name, path=path, call=call)
    for param_name, param in signature_params.items():
        # 忽略掉注解为Request的参数
        if add_non_field_param(param=param, dependant=dependant):
            continue
        # 如果默认值还是依赖注入对象则递归加入到顶层的依赖对象形成依赖树
        if isinstance(param.default, params.Depends):
            sub_dependant = get_param_dependant(param=param, path=path)
            dependant.dependencies.append(sub_dependant)
            continue
        # 即不是request也不是依赖注入对象, 例如, 路径参数,查询参数, 请求体
        param_field = get_param_field(
            param=param, default_field_info=params.Query, param_name=param_name
        )
        # 获取所有路径参数名
        path_param_names = get_path_param_names(path)
        # 参数名如果在路径参数名中时表示是路径字段
        if param_name in path_param_names:
            # 如果默认值是Path对象就不忽略默认值, 否则忽略
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
            # 把param_field添加到对应的param中
            add_param_to_field(field=param_field, dependant=dependant)
        # 不是路径参数是标准参数就作为查询参数
        elif is_scalar_field(field=param_field):
            add_param_to_field(field=param_field, dependant=dependant)
        # 默认值是查询参数或头部参数,作为对应头部和查询参数
        elif isinstance(param.default, (params.Query, params.Header)) and is_scalar_sequence_field(param_field):
            add_param_to_field(field=param_field, dependant=dependant)
        # 剩下的就作为请求体的参数
        else:
            dependant.body_params.append(param_field)
        return dependant
