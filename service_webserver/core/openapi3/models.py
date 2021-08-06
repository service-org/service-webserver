#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import typing as t

from enum import Enum
from pydantic import Field
from pydantic import AnyUrl
from pydantic import EmailStr
from pydantic import BaseModel


class Contact(BaseModel):
    """ https://swagger.io/specification/#contactObject """

    name: t.Optional[t.Text] = None
    url: t.Optional[AnyUrl] = None
    email: t.Optional[EmailStr] = None


class License(BaseModel):
    """ https://swagger.io/specification/#licenseObject """

    name: t.Text
    url: t.Optional[AnyUrl] = None


class Info(BaseModel):
    """ https://swagger.io/specification/#info-object """

    title: t.Text
    description: t.Optional[t.Text] = None
    termsOfService: t.Optional[t.Text] = None
    contact: t.Optional[Contact] = None
    license: t.Optional[License] = None
    version: t.Text


class ServerVariable(BaseModel):
    """ https://swagger.io/specification/#server-variable-object """

    enum: t.Optional[t.List[t.Text]] = None
    default: t.Text
    description: t.Optional[t.Text] = None


class Server(BaseModel):
    """ https://swagger.io/specification/#server-object """

    url: t.Union[AnyUrl, t.Text]
    description: t.Optional[t.Text] = None
    variables: t.Optional[t.Dict[t.Text, ServerVariable]] = None


class Reference(BaseModel):
    """ https://swagger.io/specification/#reference-object """

    ref: t.Text = Field(..., alias='$ref')


class Discriminator(BaseModel):
    """ https://swagger.io/specification/#discriminator-object """

    propertyName: t.Text
    mapping: t.Optional[t.Dict[t.Text, t.Text]] = None


class XML(BaseModel):
    """ https://swagger.io/specification/#xml-object """

    name: t.Optional[t.Text] = None
    namespace: t.Optional[t.Text] = None
    prefix: t.Optional[t.Text] = None
    attribute: t.Optional[bool] = None
    wrapped: t.Optional[bool] = None


class ExternalDocumentation(BaseModel):
    """ https://swagger.io/specification/#external-documentation-object """

    description: t.Optional[t.Text] = None
    url: AnyUrl


class SchemaBase(BaseModel):
    """ https://swagger.io/specification/#schema-object """

    ref: t.Optional[t.Text] = Field(None, alias='$ref')
    title: t.Optional[t.Text] = None
    multipleOf: t.Optional[float] = None
    maximum: t.Optional[float] = None
    exclusiveMaximum: t.Optional[float] = None
    minimum: t.Optional[float] = None
    exclusiveMinimum: t.Optional[float] = None
    maxLength: t.Optional[int] = Field(None, gte=0)
    minLength: t.Optional[int] = Field(None, gte=0)
    pattern: t.Optional[t.Text] = None
    maxItems: t.Optional[int] = Field(None, gte=0)
    minItems: t.Optional[int] = Field(None, gte=0)
    uniqueItems: t.Optional[bool] = None
    maxProperties: t.Optional[int] = Field(None, gte=0)
    minProperties: t.Optional[int] = Field(None, gte=0)
    required: t.Optional[t.List[t.Text]] = None
    enum: t.Optional[t.List[t.Any]] = None
    type: t.Optional[t.Text] = None
    allOf: t.Optional[t.List[t.Any]] = None
    oneOf: t.Optional[t.List[t.Any]] = None
    anyOf: t.Optional[t.List[t.Any]] = None
    not_: t.Optional[t.Any] = Field(None, alias='not')
    items: t.Optional[t.Any] = None
    properties: t.Optional[t.Dict[t.Text, t.Any]] = None
    additionalProperties: t.Optional[t.Union[t.Dict[t.Text, t.Any], bool]] = None
    description: t.Optional[t.Text] = None
    format: t.Optional[t.Text] = None
    default: t.Optional[t.Any] = None
    nullable: t.Optional[bool] = None
    discriminator: t.Optional[Discriminator] = None
    readOnly: t.Optional[bool] = None
    writeOnly: t.Optional[bool] = None
    xml: t.Optional[XML] = None
    externalDocs: t.Optional[ExternalDocumentation] = None
    example: t.Optional[t.Any] = None
    deprecated: t.Optional[bool] = None

    class Config:
        """ https://pydantic-docs.helpmanual.io/usage/model_config/ """

        extra: t.Text = 'allow'


class Schema(SchemaBase):
    """ https://swagger.io/specification/#schema-object """

    allOf: t.Optional[t.List[SchemaBase]] = None
    oneOf: t.Optional[t.List[SchemaBase]] = None
    anyOf: t.Optional[t.List[SchemaBase]] = None
    not_: t.Optional[SchemaBase] = Field(None, alias='not')
    items: t.Optional[SchemaBase] = None
    properties: t.Optional[t.Dict[t.Text, SchemaBase]] = None
    additionalProperties: t.Optional[t.Union[t.Dict[t.Text, t.Any], bool]] = None


class Example(BaseModel):
    """ https://swagger.io/specification/#example-object """

    summary: t.Optional[t.Text] = None
    description: t.Optional[t.Text] = None
    value: t.Optional[t.Any] = None
    externalValue: t.Optional[AnyUrl] = None


class ParameterInType(Enum):
    """ https://swagger.io/specification/#parameter-object """

    query = 'query'
    header = 'header'
    path = 'path'
    cookie = 'cookie'


class Encoding(BaseModel):
    """ https://swagger.io/specification/#encoding-object """

    contentType: t.Optional[t.Text] = None
    # Workaround OpenAPI recursive reference, using t.Any
    headers: t.Optional[t.Dict[t.Text, t.Union[t.Any, Reference]]] = None
    style: t.Optional[t.Text] = None
    explode: t.Optional[bool] = None
    allowReserved: t.Optional[bool] = None


class MediaType(BaseModel):
    """ https://swagger.io/specification/#media-type-object """

    schema_: t.Optional[t.Union[Schema, Reference]] = Field(None, alias='schema')
    example: t.Optional[t.Any] = None
    examples: t.Optional[t.Dict[t.Text, t.Union[Example, Reference]]] = None
    encoding: t.Optional[t.Dict[t.Text, Encoding]] = None


class ParameterBase(BaseModel):
    """ https://swagger.io/specification/#parameter-object """

    description: t.Optional[t.Text] = None
    required: t.Optional[bool] = None
    deprecated: t.Optional[bool] = None
    # Serialization rules for simple scenarios
    style: t.Optional[t.Text] = None
    explode: t.Optional[bool] = None
    allowReserved: t.Optional[bool] = None
    schema_: t.Optional[t.Union[Schema, Reference]] = Field(None, alias='schema')
    example: t.Optional[t.Any] = None
    examples: t.Optional[t.Dict[t.Text, t.Union[Example, Reference]]] = None
    # Serialization rules for more complex scenarios
    content: t.Optional[t.Dict[t.Text, MediaType]] = None


class Parameter(ParameterBase):
    """ https://swagger.io/specification/#parameter-object """

    name: t.Text
    in_: ParameterInType = Field(..., alias='in')


class Header(ParameterBase):
    """ https://swagger.io/specification/#header-object """
    pass


# Workaround OpenAPI recursive reference
class EncodingWithHeaders(Encoding):
    """ https://swagger.io/specification/#encoding-object """

    headers: t.Optional[t.Dict[t.Text, t.Union[Header, Reference]]] = None


class RequestBody(BaseModel):
    """ https://swagger.io/specification/#request-body-object """

    description: t.Optional[t.Text] = None
    content: t.Dict[t.Text, MediaType]
    required: t.Optional[bool] = None


class Link(BaseModel):
    """ https://swagger.io/specification/#link-object """

    operationRef: t.Optional[t.Text] = None
    operationId: t.Optional[t.Text] = None
    parameters: t.Optional[t.Dict[t.Text, t.Union[t.Any, t.Text]]] = None
    requestBody: t.Optional[t.Union[t.Any, t.Text]] = None
    description: t.Optional[t.Text] = None
    server: t.Optional[Server] = None


class Response(BaseModel):
    """ https://swagger.io/specification/#response-object """

    description: t.Text
    headers: t.Optional[t.Dict[t.Text, t.Union[Header, Reference]]] = None
    content: t.Optional[t.Dict[t.Text, MediaType]] = None
    links: t.Optional[t.Dict[t.Text, t.Union[Link, Reference]]] = None


class Operation(BaseModel):
    """ https://swagger.io/specification/#operation-object """

    tags: t.Optional[t.List[t.Text]] = None
    summary: t.Optional[t.Text] = None
    description: t.Optional[t.Text] = None
    externalDocs: t.Optional[ExternalDocumentation] = None
    operationId: t.Optional[t.Text] = None
    parameters: t.Optional[t.List[t.Union[Parameter, Reference]]] = None
    requestBody: t.Optional[t.Union[RequestBody, Reference]] = None
    responses: t.Dict[t.Text, Response]
    # Workaround OpenAPI recursive reference
    callbacks: t.Optional[t.Dict[t.Text, t.Union[t.Dict[t.Text, t.Any], Reference]]] = None
    deprecated: t.Optional[bool] = None
    security: t.Optional[t.List[t.Dict[t.Text, t.List[t.Text]]]] = None
    servers: t.Optional[t.List[Server]] = None


class PathItem(BaseModel):
    """ https://swagger.io/specification/#path-item-object """

    ref: t.Optional[t.Text] = Field(None, alias='$ref')
    summary: t.Optional[t.Text] = None
    description: t.Optional[t.Text] = None
    get: t.Optional[Operation] = None
    put: t.Optional[Operation] = None
    post: t.Optional[Operation] = None
    delete: t.Optional[Operation] = None
    options: t.Optional[Operation] = None
    head: t.Optional[Operation] = None
    patch: t.Optional[Operation] = None
    trace: t.Optional[Operation] = None
    servers: t.Optional[t.List[Server]] = None
    parameters: t.Optional[t.List[t.Union[Parameter, Reference]]] = None


# Workaround OpenAPI recursive reference
class OperationWithCallbacks(BaseModel):
    """ https://swagger.io/specification/#operation-object """

    callbacks: t.Optional[t.Dict[t.Text, t.Union[t.Dict[t.Text, PathItem], Reference]]] = None


class SecuritySchemeType(Enum):
    """ https://swagger.io/specification/#security-scheme-object """

    apiKey = 'apiKey'
    http = 'http'
    oauth2 = 'oauth2'
    openIdConnect = 'openIdConnect'


class SecurityBase(BaseModel):
    """ https://swagger.io/specification/#security-scheme-object """

    type_: SecuritySchemeType = Field(..., alias='type')
    description: t.Optional[t.Text] = None


class APIKeyIn(Enum):
    """ https://swagger.io/specification/#security-scheme-object """

    query = 'query'
    header = 'header'
    cookie = 'cookie'


class APIKey(SecurityBase):
    """ https://swagger.io/specification/#security-scheme-object """

    type_ = Field(SecuritySchemeType.apiKey, alias='type')
    in_: APIKeyIn = Field(..., alias='in')
    name: t.Text


class HTTPBase(SecurityBase):
    """ https://swagger.io/specification/#security-scheme-object """
    type_ = Field(SecuritySchemeType.http, alias='type')
    scheme: t.Text


class HTTPBearer(HTTPBase):
    """ https://swagger.io/specification/#security-scheme-object """

    scheme = 'bearer'
    bearerFormat: t.Optional[t.Text] = None


class OAuthFlow(BaseModel):
    """ https://swagger.io/specification/#security-scheme-object """

    refreshUrl: t.Optional[t.Text] = None
    scopes: t.Dict[t.Text, t.Text] = {}


class OAuthFlowImplicit(OAuthFlow):
    """ https://swagger.io/specification/#security-scheme-object """

    authorizationUrl: t.Text


class OAuthFlowPassword(OAuthFlow):
    """ https://swagger.io/specification/#security-scheme-object """

    tokenUrl: t.Text


class OAuthFlowClientCredentials(OAuthFlow):
    """ https://swagger.io/specification/#security-scheme-object """

    tokenUrl: t.Text


class OAuthFlowAuthorizationCode(OAuthFlow):
    """ https://swagger.io/specification/#security-scheme-object """

    authorizationUrl: t.Text
    tokenUrl: t.Text


class OAuthFlows(BaseModel):
    """ https://swagger.io/specification/#security-scheme-object """

    implicit: t.Optional[OAuthFlowImplicit] = None
    password: t.Optional[OAuthFlowPassword] = None
    clientCredentials: t.Optional[OAuthFlowClientCredentials] = None
    authorizationCode: t.Optional[OAuthFlowAuthorizationCode] = None


class OAuth2(SecurityBase):
    """ https://swagger.io/specification/#security-scheme-object """

    type_ = Field(SecuritySchemeType.oauth2, alias='type')
    flows: OAuthFlows


class OpenIdConnect(SecurityBase):
    """ https://swagger.io/specification/#security-scheme-object """

    type_ = Field(SecuritySchemeType.openIdConnect, alias='type')
    openIdConnectUrl: t.Text


SecurityScheme = t.Union[APIKey, HTTPBase, OAuth2, OpenIdConnect, HTTPBearer]


class Components(BaseModel):
    """ https://swagger.io/specification/#components-object """

    schemas: t.Optional[t.Dict[t.Text, t.Union[Schema, Reference]]] = None
    responses: t.Optional[t.Dict[t.Text, t.Union[Response, Reference]]] = None
    parameters: t.Optional[t.Dict[t.Text, t.Union[Parameter, Reference]]] = None
    examples: t.Optional[t.Dict[t.Text, t.Union[Example, Reference]]] = None
    requestBodies: t.Optional[t.Dict[t.Text, t.Union[RequestBody, Reference]]] = None
    headers: t.Optional[t.Dict[t.Text, t.Union[Header, Reference]]] = None
    securitySchemes: t.Optional[t.Dict[t.Text, t.Union[SecurityScheme, Reference]]] = None
    links: t.Optional[t.Dict[t.Text, t.Union[Link, Reference]]] = None
    callbacks: t.Optional[t.Dict[t.Text, t.Union[t.Dict[t.Text, PathItem], Reference]]] = None


class Tag(BaseModel):
    """ https://swagger.io/specification/#tag-object """

    name: t.Text
    description: t.Optional[t.Text] = None
    externalDocs: t.Optional[ExternalDocumentation] = None


class OpenAPI(BaseModel):
    """  https://swagger.io/specification/ """

    openapi: t.Text
    info: Info
    servers: t.Optional[t.List[Server]] = None
    paths: t.Dict[t.Text, PathItem]
    components: t.Optional[Components] = None
    security: t.Optional[t.List[t.Dict[t.Text, t.List[t.Text]]]] = None
    tags: t.Optional[t.List[Tag]] = None
    externalDocs: t.Optional[ExternalDocumentation] = None
