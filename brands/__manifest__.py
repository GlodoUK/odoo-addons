{
    "name": "Brands",
    "version": "18.0.1.0.0",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["sale"],
    "data": [
        "data/res_partner_data.xml",  # Order Important
        "data/glo_brand_data.xml",
        "report/sale_report_views.xml",
        "report/account_invoice_report_views.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/glo_brand_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        # "views/report_templates/external_layout_bold.xml",
        # "views/report_templates/external_layout_boxed.xml",
        # "views/report_templates/external_layout_standard.xml",
        # "views/report_templates/external_layout_striped.xml",
    ],
    "license": "Other proprietary",
}
