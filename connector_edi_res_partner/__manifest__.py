{
    "name": "connector_edi_res_partner",
    "summary": "EDI Partner binding module",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": [
        "base_sparse_field",
        "connector_edi",
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "views/edi_res_partner.xml",
    ],
    "license": "Other proprietary",
}
