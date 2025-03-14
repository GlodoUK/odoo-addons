{
    "name": "Helpdesk Account Move Link",
    "version": "16.0.1.0.0",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Links Account Moves to Helpdesk Tickets",
    "depends": [
        "helpdesk",
        "account",
    ],
    "data": [
        "reports/report_invoice_document.xml",
        "views/account_move.xml",
        "views/helpdesk_ticket.xml",
    ],
}
