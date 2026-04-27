{
    "name": "Website Hierarchical Category Search",
    "version": "19.0.1.0.0",
    "category": "Website/eCommerce",
    "summary": "Website snippet: cascading dropdowns to search products by category"
    " hierarchy",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "depends": ["website", "website_sale"],
    "data": [
        "views/product_public_category_views.xml",
        "views/snippets/s_category_search.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_category_heirarchy_search/static/src/components/*.js",
            "website_category_heirarchy_search/static/src/interactions/*.js",
            "website_category_heirarchy_search/static/src/scss/*.scss",
        ],
        "website.website_builder_assets": [
            "website_category_heirarchy_search/static/src/website_builder/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
