import json

from odoo import api, fields, models


class EdiSaleOrderLine(models.Model):
    _name = "edi.sale.order.line"
    _description = "EDI Sale Order Line Binding"
    _inherit = "edi.binding"
    _inherits = {"sale.order.line": "odoo_id"}

    edi_order_id = fields.Many2one(
        "edi.sale.order",
        index=True,
        ondelete="cascade",
    )

    odoo_id = fields.Many2one(
        "sale.order.line",
        "Sale Order Line",
        ondelete="cascade",
        required=True,
    )

    edi_line_ref = fields.Char()

    edi_metadata = fields.Serialized()

    # XXX: Temporary workaround to display serialized field on frontend
    edi_metadata_string = fields.Char(
        compute="_compute_edi_metadata_string",
        string="Metadata",
    )

    def _compute_edi_metadata_string(self):
        for line in self:
            line.edi_metadata_string = json.dumps(line.edi_metadata)

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

        return super().create(vals_list)
