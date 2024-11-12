import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'depends_override': {
            "sale_order_hold": "git+https://github.com/GlodoUK/sale@15.0#subdirectory=setup/sale_order_hold"
        }
    }
)
