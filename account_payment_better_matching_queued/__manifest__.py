{
    "version": "15.0.1.0.0",
    "name": "account_payment_better_matching_queued",
    "summary": "Adds queued support to account_payment_better_matching",
    "category": "Finance",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "depends": [
        "account_payment_better_matching",
        # "account_move_line_reconcile_queued",
    ],
    "data": [
        "wizards/account_payment_better_matching.xml",
        "data/account_move_line_partial_reconcile_job.xml",
    ],
    "demo": [],
}
