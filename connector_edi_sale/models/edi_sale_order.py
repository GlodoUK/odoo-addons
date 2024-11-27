import json

from odoo import api, fields, models


class EdiSaleOrder(models.Model):
    _name = "edi.sale.order"
    _inherit = "edi.binding"
    _inherits = {"sale.order": "odoo_id"}

    odoo_id = fields.Many2one(
        "sale.order", string="Sale Order", required=True, ondelete="cascade"
    )

    edi_message_id = fields.Many2one(
        "edi.message",
        index=True,
        required=True,
        auto_join=True,
    )

    edi_external_id = fields.Char(string="EDI External Ref")

    edi_order_line_ids = fields.One2many(
        "edi.sale.order.line",
        "edi_order_id",
    )
    edi_metadata = fields.Serialized()
    # XXX: Temporary workaround to display serialized field on frontend
    edi_metadata_string = fields.Char(
        compute="_compute_edi_metadata_string",
        string="Metadata",
    )

    def _compute_edi_metadata_string(self):
        for record in self:
            record.edi_metadata_string = json.dumps(record.edi_metadata)

    @api.model
    def create(self, vals):
        # Makes sure partner_invoice_id', 'partner_shipping_id' and
        # 'pricelist_id' are defined
        if any(
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

        return super(EdiSaleOrder, self).create(vals)

    def action_confirm(self):
        self.mapped("odoo_id").action_confirm()

    def action_cancel(self):
        self.mapped("odoo_id").action_cancel()


class EdiSaleOrderLine(models.Model):
    _name = "edi.sale.order.line"
    _inherit = "edi.binding"
    _inherits = {"sale.order.line": "odoo_id"}

    edi_order_id = fields.Many2one("edi.sale.order", index=True)

    odoo_id = fields.Many2one(
        "sale.order.line", string="Sale Order Line", required=True, ondelete="cascade"
    )

    edi_line_ref = fields.Char()
    edi_metadata = fields.Serialized()
    # XXX: Temporary workaround to display serialized field on frontend
    edi_metadata_string = fields.Char(
        compute="_compute_edi_metadata_string",
        string="Metadata",
    )

    def _compute_edi_metadata_string(self):
        for record in self:
            record.edi_metadata_string = json.dumps(record.edi_metadata)

    @api.model_create_multi
    def create(self, vals_list):
        fields_to_filter = self.env["sale.order.line"]._fields.keys()

        for vals in vals_list:
            if "order_id" not in vals:
                vals["order_id"] = (
                    self.env["edi.sale.order"].browse(vals["edi_order_id"]).odoo_id.id
                )

            vals.update(
                self.env["sale.order.line"]._prepare_add_missing_fields(
                    {k: v for k, v in vals.items() if k not in fields_to_filter}
                )
            )

        return super(EdiSaleOrderLine, self).create(vals_list)
