{
    "name": "Helpdesk Sale Order Link",
    "version": "16.0.1.0.0",
    "category": "Services/Helpdesk",
    "author": "Glo Networks",
    "website": "https://github.com/GlodoUK/odoo-addons",
    "license": "Other proprietary",
    "summary": "Links Sales Orders to Helpdesk Tickets",
    "depends": ["helpdesk", "sale"],
    "data": [
        "reports/report_sale_document.xml",
        "views/helpdesk_ticket.xml",
        "views/sale_order.xml",
        "views/helpdesk_ticket_portal.xml",
    ],
}
