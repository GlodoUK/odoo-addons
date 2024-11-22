{
    'name': "product_stock_orderpoint_link",
    'summary': """
    Adds a smart button on products and templates to go to their reordering
    rules, and allows reorderpoints to be created from product templates and
    variants.
    """,
    'author': "Glo Networks",
    'website': "https://github.com/GlodoUK/odoo-addons",
    'category': 'Uncategorized',
    'version': '12.0.1.0.0',
    'depends': ['stock'],
    'data': [
        'views/views.xml',
    ],
    'license': 'AGPL-3',
}
