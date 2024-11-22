from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GloBrand(models.Model):
    """
    Brand
    """

    _name = "glo.brand"
    _order = "name"

    name = fields.Char("Name", required=True)
    logo = fields.Binary("Logo")

    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    street = fields.Char(related="partner_id.street", store=True, readonly=True)
    street2 = fields.Char(related="partner_id.street2", store=True, readonly=True)
    zip = fields.Char(related="partner_id.zip", store=True, readonly=True)
    city = fields.Char(related="partner_id.city", store=True, readonly=True)
    state_id = fields.Many2one(related="partner_id.state_id", store=True, readonly=True)
    country_id = fields.Many2one(
        related="partner_id.country_id", store=True, readonly=True
    )
    email = fields.Char(related="partner_id.email", store=True, readonly=True)
    phone = fields.Char(related="partner_id.phone", store=True, readonly=True)
    website = fields.Char(related="partner_id.website", store=True, readonly=True)
    vat = fields.Char(related="partner_id.vat", store=True, readonly=True)

    is_default = fields.Boolean(default=False)
    active = fields.Boolean(default=True)

    @api.onchange("partner_id")
    @api.multi
    def _onchange_partner_id(self):
        for record in self:
            if record.name != record.partner_id.name:
                record.name = record.partner_id.name

    @api.model
    def _change_report_layout_id(self):
        self.env["res.config.settings"].create(
            {
                "external_report_layout_id": self.env.ref(
                    "web.external_layout_boxed"
                ).id
            }
        )

    @api.model
    def get_default_record(self):
        return self.env["glo.brand"].search([("is_default", "=", True)], limit=1)

    @api.constrains('is_default')
    def _check_is_default(self):
        if not self.is_default:
            return

        count = self.search_count([('is_default', '=', True)])
        if count > 1:
            raise ValidationError(_('Can only have 1 default!'))


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        "glo.brand", string="Brand", help="Select a brand for this product"
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_default_brand(self):
        return self.env['glo.brand'].get_default_record()

    brand_id = fields.Many2one(
        "glo.brand",
        string="Brand",
        help="Select a brand for this sale",
        default=_get_default_brand,
    )

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        vals = super(SaleOrder, self)._prepare_invoice()

        if self.brand_id:
            vals["brand_id"] = self.brand_id.id

        return vals


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    brand_id = fields.Many2one(
        "glo.brand", string="Brand", help="Select a brand for this Invoice"
    )
