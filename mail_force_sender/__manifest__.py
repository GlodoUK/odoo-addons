{
    'name': 'mail_force_sender',
    'summary': """Force the outgoing email address, overriding Odoo's default
    behaviour of using the initiating user's email.""",
    'version': '12.0.1.1.0',
    'category': 'Discuss',
    'author': 'Glo Networks',
    'website': 'https://github.com/GlodoUK/odoo-addons',
    'depends': ['mail'],
    'data': ['data/ir_config_parameter.xml', 'views/res_config_settings.xml'],
    'license': 'Other proprietary',
}
