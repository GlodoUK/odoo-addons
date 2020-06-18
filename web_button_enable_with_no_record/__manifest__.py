# -*- coding: utf-8 -*-
{
    "version": "0.1",
    "name": "web_button_enable_with_no_record",
    "summary": "Allows you to force Odoo to enable a button, even if there is no record",
    "category": "Extra Tools",
    "images": [],
    "application": False,
    "author": "Glo Networks",
    "website": "https://www.glo.systems/",
    "license": "LGPL-3",
    "depends": ["web"],
    "external_dependencies": {"python": [], "bin": []},
    "data": ["views/views.xml"],
    "qweb": [],
    "demo": [],
    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "uninstall_hook": None,
    "auto_install": False,
    "installable": True,
    "description": """
Allows you to force Odoo to enable a button, even if there is no record
"""
}
