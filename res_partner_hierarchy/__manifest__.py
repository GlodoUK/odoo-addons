{
    "name": "res_partner_hierarchy",
    "summary": "Arbitrarily deep partner parent/child tree, independent of parent_id",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": [
        "contacts",
        "web_hierarchy",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_hierarchy_type.xml",
        "views/res_partner.xml",
        "views/res_partner_hierarchy.xml",
    ],
    "license": "LGPL-3",
}
