#! -*- coding: utf-8 -*-
#
# author: forcemain@163.com

from __future__ import annotations


def get_swagger_payload():
    """ 获取swagger载体 """
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css"
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>Service - swagger-ui</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const ui = SwaggerUIBundle({{
        url: '/openapi.json',
    """
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
    html += """
    </script>
    </body>
    </html>
    """
    return html


def get_redoc_payload():
    """ 获取redoc载体 """
    redoc_js_url: str = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    redoc_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <title>Service - redoc-ui</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    """
    html += f"""
    <link rel="shortcut icon" href="{redoc_favicon_url}">
    <!--
    ReDoc doesn't change outer page styles
    -->
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
    </head>
    <body>
    <redoc spec-url="/redoc"></redoc>
    <script src="{redoc_js_url}"> </script>
    </body>
    </html>
    """
    return html
