#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

import typing as t

from pydantic import BaseModel
from pydantic import create_model

if t.TYPE_CHECKING:
    from pydantic.fields import ModelField
    from .depent.models import Dependant

from pydantic.fields import ModelField

from . import params
from .depent.models import Dependant
from .depent.helper import create_response_field

def get_flat_dependant(
        dependant: Dependant,
) -> Dependant:
    flat_dependant = Dependant(
        path_params=dependant.path_params.copy(),
        query_params=dependant.query_params.copy(),
        header_params=dependant.header_params.copy(),
        cookie_params=dependant.cookie_params.copy(),
        body_params=dependant.body_params.copy(),
        path=dependant.path
    )
    for sub_dependant in dependant.dependencies:
        flat_sub = get_flat_dependant(sub_dependant)
        flat_dependant.path_params.extend(flat_sub.path_params)
        flat_dependant.query_params.extend(flat_sub.query_params)
        flat_dependant.header_params.extend(flat_sub.header_params)
        flat_dependant.cookie_params.extend(flat_sub.cookie_params)
        flat_dependant.body_params.extend(flat_sub.body_params)
    return flat_dependant


def get_body_field(
        *,
        dependant: Dependant,
        name: t.Text
) -> t.Optional[ModelField]:
    flat_dependant = get_flat_dependant(dependant)
    if not flat_dependant.body_params:
        return None
    for param in flat_dependant.body_params:
        setattr(param.field_info, 'embed', True)
    model_name = f'Body_{name}'
    BodyModel: t.Type[BaseModel] = create_model(model_name)
    for f in flat_dependant.body_params:
        BodyModel.__fields__[f.name] = f
    required = any(True for f in flat_dependant.body_params if f.required)
    BodyFieldInfo_kwargs: Dict[str, Any] = dict(default=None)
    if any(isinstance(f.field_info, params.File) for f in flat_dependant.body_params):
        BodyFieldInfo: t.Type[params.Body] = params.File
    elif any(isinstance(f.field_info, params.Form) for f in flat_dependant.body_params):
        BodyFieldInfo = params.Form
    else:
        BodyFieldInfo = params.Body

        body_param_media_types = [
            getattr(f.field_info, "media_type")
            for f in flat_dependant.body_params
            if isinstance(f.field_info, params.Body)
        ]
        if len(set(body_param_media_types)) == 1:
            BodyFieldInfo_kwargs["media_type"] = body_param_media_types[0]
    final_field = create_response_field(
        name="body",
        type_=BodyModel,
        required=required,
        alias="body",
        field_info=BodyFieldInfo(**BodyFieldInfo_kwargs),
    )
    return final_field
