from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_auto_invoice_credit_notes = fields.Boolean(
        string="Auto-Raise Credit Notes",
        default=True,
        help="When enabled, the automatic invoicing run raises credit notes for "
        "pending negative quantities (returns, downward corrections). When "
        "disabled, only positive quantities are invoiced automatically and "
        "credit notes have to be raised by hand.",
    )
