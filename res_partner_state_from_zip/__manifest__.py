{
    "name": "res_partner_state_from_zip",
    "summary": "Fill a contact's blank state from its zip, by longest prefix",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Hidden/Tools",
    "version": "19.0.1.0.0",
    "depends": [
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_state_from_zip_prefix_views.xml",
        "data/ir_actions_server.xml",
        "data/res_partner_state_from_zip_prefix_gb.xml",
    ],
    "license": "Other proprietary",
}
