from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # NOTE: ``fields.Monetary`` is not one of ``COMPANY_DEPENDENT_FIELDS``, so a
    # company-dependent amount has to be a Float rendered with the monetary
    # widget - the same trick core uses for ``res.partner.credit_limit``. The
    # currency it is read against is ``purchase_mov_currency_id`` below.
    property_purchase_mov = fields.Float(
        string="Minimum Order Value",
        company_dependent=True,
        help="Minimum value a purchase order for this vendor must reach before"
        " it can be confirmed. Expressed in the vendor's Supplier Currency,"
        " falling back to the company currency. 0 means no minimum.",
    )
    purchase_mov_currency_id = fields.Many2one(
        "res.currency",
        string="Minimum Order Value Currency",
        compute="_compute_purchase_mov_currency_id",
        help="Currency the Minimum Order Value is expressed in.",
    )

    # ``property_purchase_currency_id`` is company_dependent and the fallback is
    # read off ``env.company``, but a computed field does not inherit
    # depends_context from its dependencies - it has to be declared here or the
    # cache would hand one company's currency to another.
    @api.depends("property_purchase_currency_id")
    @api.depends_context("company")
    def _compute_purchase_mov_currency_id(self):
        company_currency = self.env.company.currency_id

        for partner in self:
            partner.purchase_mov_currency_id = (
                partner.property_purchase_currency_id or company_currency
            )
