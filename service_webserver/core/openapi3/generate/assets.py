#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations

import json
import typing as t

from service_webserver.core.encoder import jsonable_encoder

SWAGGER_UI_OAUTH2_REDIRECT_HTML = """
<!DOCTYPE html>
<html lang="en-US">
    <body onload="run()">
    </body>
</html>
<script>
    'use strict';
    function run () {
        var oauth2 = window.opener.swaggerUIRedirectOauth2;
        var sentState = oauth2.state;
        var redirectUrl = oauth2.redirectUrl;
        var isValid, qp, arr;

        if (/code|token|error/.test(window.location.hash)) {
            qp = window.location.hash.substring(1);
        } else {
            qp = location.search.substring(1);
        }

        arr = qp.split("&")
        arr.forEach(function (v,i,_arr) { _arr[i] = '"' + v.replace('=', '":"') + '"';})
        qp = qp ? JSON.parse('{' + arr.join() + '}',
                function (key, value) {
                    return key === "" ? value : decodeURIComponent(value)
                }
        ) : {}

        isValid = qp.state === sentState

        if ((
        oauth2.auth.schema.get("flow") === "accessCode"||
        oauth2.auth.schema.get("flow") === "authorizationCode"
        ) && !oauth2.auth.code) {
            if (!isValid) {
                oauth2.errCb({
                    authId: oauth2.auth.name,
                    source: "auth",
                    level: "warning",
                    message: "Authorization may be unsafe, Passed state wasn't returned from auth server"
                });
            }

            if (qp.code) {
                delete oauth2.state;
                oauth2.auth.code = qp.code;
                oauth2.callback({auth: oauth2.auth, redirectUrl: redirectUrl});
            } else {
                let oauthErrorMsg
                if (qp.error) {
                    oauthErrorMsg = "["+qp.error+"]: " +
                        (qp.error_description ? qp.error_description+ ". " : "no accessCode from the server. ") +
                        (qp.error_uri ? "More info: "+qp.error_uri : "");
                }

                oauth2.errCb({
                    authId: oauth2.auth.name,
                    source: "auth",
                    level: "error",
                    message: oauthErrorMsg || "[Authorization failed]: no accessCode received from the server"
                });
            }
        } else {
            oauth2.callback({auth: oauth2.auth, token: qp, isValid: isValid, redirectUrl: redirectUrl});
        }
        window.close();
    }
</script>
"""


def get_swagger_ui_oauth2_redirect_html() -> t.Text:
    """ 获取Swagger Ui OAuth2跳转页

    @return: t.Text
    """
    html = SWAGGER_UI_OAUTH2_REDIRECT_HTML
    return html


def get_swagger_ui_html(
        *, title: t.Text,
        openapi_url: t.Text,
        oauth2_redirect_url: t.Optional[t.Text] = None,
        oauth2_init: t.Optional[t.Dict[t.Text, t.Any]] = None,
        swagger_favicon_url: t.Optional[t.Text] = None,
        swagger_css_url: t.Optional[t.Text] = None,
        swagger_js_url: t.Optional[t.Text] = None
) -> t.Text:
    """ 获取SwaggerUI接口列表页内容

    @param title: swagger ui文档标题
    @param openapi_url: openapi3 json地址
    @param oauth2_redirect_url: 跳转url
    @param oauth2_init: 认证初始化
    @param swagger_favicon_url: 图标地址
    @param swagger_css_url: 样式的地址
    @param swagger_js_url:  JS的 地址
    @return: t.Text
    """
    swagger_favicon_url = swagger_favicon_url or 'https://fastapi.tiangolo.com/img/favicon.png'
    swagger_css_url = swagger_css_url or 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css'
    swagger_js_url = swagger_js_url or 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js'
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
    """
    if oauth2_redirect_url:
        html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"
    html += """
        dom_id: '#swagger-ui',
        presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout",
        deepLinking: true,
        showExtensions: true,
        showCommonExtensions: true
    })"""
    if oauth2_init:
        html += f"""
        ui.initOAuth({json.dumps(jsonable_encoder(oauth2_init))})
        """
    html += """
    </script>
    </body>
    </html>
    """
    return html


def get_redoc_html(
        *, title: t.Text,
        openapi_url: t.Text,
        redoc_favicon_url: t.Optional[t.Text] = None,
        redoc_js_url: t.Optional[t.Text] = None,
        with_google_fonts: bool = True
) -> t.Text:
    """ 获取Redoc UI接口列表页内容

    @param title: redoc ui文档标题
    @param openapi_url: openapi3 json地址
    @param redoc_js_url: JS的地址
    @param redoc_favicon_url: 图标地址
    @param with_google_fonts: 谷歌字体
    @return: t.Text
    """
    redoc_favicon_url = redoc_favicon_url or 'https://fastapi.tiangolo.com/img/favicon.png'
    redoc_js_url = redoc_js_url or 'https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js'
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>{title}</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    """
    if with_google_fonts:
        html += """
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    """
    html += f"""
    <link rel="shortcut icon" href="{redoc_favicon_url}">
    <!--
    ReDoc doesn't change outer page styles
    -->
    <style>
    body {{margin: 0; padding: 0;}}
    </style>
    </head>
    <body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="{redoc_js_url}"> </script>
    </body>
    </html>
    """
    return html
