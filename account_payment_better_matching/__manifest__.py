{
    'version': "12.0.1.1.0",
    'name': "account_payment_better_matching",
    'summary': "A better interface for bulk, but manual payment matching",
    'category': "Finance",
    'images': [],
    'application': False,

    'author': "Glo",
    'website': "https://github.com/GlodoUK/odoo-addons",
    'license': "Other proprietary",

    'depends': [
        'account',
    ],

    'external_dependencies': {"python": [], "bin": []},

    'data': [
        'views/views.xml',
        'wizards/account_payment_better_matching.xml'
    ],
    'qweb': [],
    'demo': [],

    'post_load': None,
    'pre_init_hook': None,
    'post_init_hook': None,
    'uninstall_hook': None,

    'auto_install': False,
    'installable': True,
}
