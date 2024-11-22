{
    'name': "purchase_filter_by_receipt_state",

    'summary': """
    Filter Purchases by receipt state
    """,

    'author': "Glo Networks",
    'website': "https://github.com/GlodoUK/odoo-addons",

    'category': 'Purchases',
    'version': '12.0.1.0.0',
    'depends': [
        'purchase_stock'
    ],

    'data': [
        'views/views.xml',
    ],

    'license': 'AGPL-3',
}
