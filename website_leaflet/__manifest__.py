{
    "name": "website_leaflet",
    "summary": "Adds a leaflet.js powered map (eventually snippet)",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "category": "Hidden",
    "version": "15.0.1.0.1",
    "depends": ["website"],
    "external_dependencies": {"python": []},
    "data": [],
    "assets": {
        "web.assets_frontend": [
            "/website_leaflet/static/lib/leaflet/leaflet.css",
            "/website_leaflet/static/src/scss/leaflet.scss",
            "/website_leaflet/static/lib/leaflet/leaflet.js",
            "/website_leaflet/static/src/js/frontend.js",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}
