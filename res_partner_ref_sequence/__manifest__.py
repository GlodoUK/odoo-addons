{
    "name": "res_partner_ref_sequence",
    "summary": "Assign partner references from rule-selected sequences",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Uncategorized",
    "version": "19.0.1.0.0",
    "depends": [
        "contacts",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/res_partner_ref_sequence_rule.xml",
        "views/res_partner_ref_sequence_rule.xml",
        "views/res_partner.xml",
    ],
    "license": "LGPL-3",
}
