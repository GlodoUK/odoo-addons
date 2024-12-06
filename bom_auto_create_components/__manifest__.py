{
    "name": "bom_auto_create_components",
    "summary": """
        Wizard to create BoM component lines based on matching product attributes""",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Inventory",
    "version": "17.0.1.0.0",
    "depends": ["product", "product_variant_configurator", "mrp"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/wizard_bom_create_components.xml",
        "views/mrp_bom.xml",
    ],
    "demo": [],
    "license": "AGPL-3",
}
