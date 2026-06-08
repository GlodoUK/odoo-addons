{
    "name": "shoehorn",
    "summary": "Repeatedly and safely bootstrap Odoo databases (odoo shoehorn)",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Technical",
    "version": "19.0.1.0.0",
    "depends": ["base"],
    "license": "Other proprietary",
    "data": [
        "security/ir.model.access.csv",
        "views/generate_wizard_views.xml",
    ],
    # The CLI command works from the addons path alone, without installing.
    # Installing this module only adds the "Generate shoehorn migration"
    # wizard under Settings > Technical.
}
