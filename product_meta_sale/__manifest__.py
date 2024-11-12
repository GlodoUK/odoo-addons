{
    "name": "product_meta_sale",
    "summary": "Glue module between product_meta and sale",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/stock-delivery",
    "category": "Sales",
    "version": "15.0.1.0.0",
    "depends": ["sale", "product_meta"],
    "data": [
        "report/sale_report_templates.xml",
        "views/product_template.xml",
        "views/sale_order.xml",
        "views/sale_portal_templates.xml",
    ],
    "license": "AGPL-3",
    "assets": {
        "web.assets_backend": [
            "product_meta_sale/static/src/js/section_and_notes_field_renderer.js",
            "product_meta_sale/static/src/css/section_and_notes_field_renderer.css",
        ],
    },
}
