{
    "name": "brands_account",
    "summary": "Extend brands functionality to account module",
    "category": "Accounting",
    "application": True,
    "version": "17.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "LGPL-3",
    "depends": ["brands", "sale"],
    "data": [
        "views/res_bank.xml",
        "views/res_partner_bank.xml",
        "views/brand_partner_payment_instruction_template.xml",
        "views/report_invoice.xml",
        "views/report_saleorder_document.xml",
        "views/sale_portal_template.xml",
    ],
}
