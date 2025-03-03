{
    'version': "12.0.1.0.1",
    'name': "web_higher_upload_limit",
    'summary': "Increases the upload limit",
    'category': "Extra Tools",
    'images': [],
    'application': False,
    "license": "LGPL-3",
    'author': "Glodo",
    'website': "https://github.com/GlodoUK/odoo-addons",
    'license': "Other proprietary",

    'depends': ['web'],
    'external_dependencies': {"python": [], "bin": []},

    'data': [
        'views/views.xml'
    ],
    'qweb': [
    ],
    'demo': [
    ],

    'post_load': None,
    'pre_init_hook': None,
    'post_init_hook': None,
    'uninstall_hook': None,

    'auto_install': False,
    'installable': True,

    'description': """
Increases the upload limit
"""
}
