import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        'depends_override': {
            "concurrency_warning": "git+https://github.com/GlodoUK/web@16.0#subdirectory=setup/concurrency_warning"
        }
    }
)
