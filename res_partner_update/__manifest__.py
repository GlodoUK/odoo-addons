{
    "name": "res_partner_update",
    "version": "19.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["base"],
    "data": [
        "security/res_groups_data.xml",
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/res_partner_update_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "res_partner_update/static/src/css/res_partner_update_kanban.scss",
        ],
    },
    "license": "LGPL-3",
}
