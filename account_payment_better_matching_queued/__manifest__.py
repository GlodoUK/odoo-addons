{
    'version': "12.0.1.0.0",
    'name': "account_payment_better_matching_queued",
    'summary': "Adds queued support to account_payment_better_matching",
    'category': "Finance",
    'images': [],
    'application': False,

    'author': "Glo",
    'website': "https://github.com/GlodoUK/odoo-addons",
    'license': "Other proprietary",

    'depends': [
        'account_payment_better_matching',
        'account_move_line_reconcile_queued',
    ],

    'external_dependencies': {"python": [], "bin": []},

    'data': [
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
