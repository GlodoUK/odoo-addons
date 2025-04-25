from odoo import _, api, fields, models

from odoo.addons.connector_edi.exceptions import EdiException


class EdiSaleOrder(models.Model):
    _name = "edi.sale.order"
    _description = "EDI Sale Order Binding"
    _inherit = "edi.binding"
    _inherits = {"sale.order": "odoo_id"}

    odoo_id = fields.Many2one(
        "sale.order",
        ondelete="cascade",
        required=True,
        string="Sale Order",
    )

    edi_message_id = fields.Many2one(
        "edi.message",
        index=True,
        required=False,
        auto_join=True,
    )

    edi_external_id = fields.Char(
        string="EDI Reference",
    )

    edi_order_line_ids = fields.One2many(
        "edi.sale.order.line",
        "edi_order_id",
    )

    # edi_metadata = fields.Serialized()
    # # XXX: Temporary workaround to display serialized field on frontend
    # edi_metadata_string = fields.Char(
    #     compute="_compute_edi_metadata_string",
    #     string="Metadata",
    # )

    # def _compute_edi_metadata_string(self):
    #     for record in self:
    #         record.edi_metadata_string = json.dumps(record.edi_metadata)

    @api.model
    def create(self, vals):
        # Makes sure partner_invoice_id', 'partner_shipping_id' and
        # 'pricelist_id' are defined
        if not vals.get("odoo_id") and any(
            f not in vals
            for f in ["partner_invoice_id", "partner_shipping_id", "pricelist_id"]
        ):
            partner = self.env["res.partner"].browse(vals.get("partner_id"))
            addr = partner.address_get(["delivery", "invoice"])
            vals["partner_invoice_id"] = vals.setdefault(
                "partner_invoice_id", addr["invoice"]
            )
            vals["partner_shipping_id"] = vals.setdefault(
                "partner_shipping_id", addr["delivery"]
            )
            vals["pricelist_id"] = vals.setdefault(
                "pricelist_id",
                partner.property_product_pricelist
                and partner.property_product_pricelist.id,
            )

        return super().create(vals)

    def action_apply_carrier(self, carrier_id, rate=True):
        self.ensure_one()

        price = 0.0
        msg = False

        if carrier_id and rate:
            vals = carrier_id.rate_shipment(self.odoo_id)
            if not vals.get("success"):
                raise EdiException(
                    _("Could not rate carrier '{carrier}': {msg}")
                    % {
                        "carrier": carrier_id,
                        "msg": vals.get("error_message") or vals.get("warning_message"),
                    }
                )
            msg = vals.get("warning_message", False)
            price = vals.get("price")

        self.odoo_id.set_delivery_line(carrier_id, price)
        self.odoo_id.write(
            {
                "recompute_delivery_price": False,
                "delivery_message": msg,
            }
        )

    def action_cancel(self):
        self.mapped("odoo_id").action_cancel()

    def action_confirm(self):
        self.mapped("odoo_id").action_confirm()

    # def action_update_prices(self):
    #     self.ensure_one()
    #     self.invalidate_cache()
    #     self.odoo_id.show_update_pricelist = True
    #     self.odoo_id.update_prices()
