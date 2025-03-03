{
    'version': "12.0.1.1.0",
    'name': "account_move_line_reconcile_queued",
    'summary': "Account move line reconcile queued",
    'category': "Finance",
    'images': [],
    'application': False,

    'author': "Glo",
    'website': "https://github.com/GlodoUK/odoo-addons",
    'license': "Other proprietary",

    'depends': [
        'account',
        'queue_job',
    ],

    'external_dependencies': {"python": [], "bin": []},

    'data': [
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
