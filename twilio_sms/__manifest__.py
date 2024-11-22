{
    "version": "15.0.2.0.0",
    "name": "twilio_sms",
    "summary": "Twilio SMS Gateway",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "depends": ["sms"],
    "external_dependencies": {"python": ["twilio", "phonenumbers"]},
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings.xml",
        "views/sms_log.xml",
    ],
}
