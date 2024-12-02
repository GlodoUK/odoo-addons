import json

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    meta_attrs = fields.Serialized()
    meta_attrs_display = fields.Char(compute="_compute_meta_attrs_display")

    @api.depends("meta_attrs")
    def _compute_meta_attrs_display(self):
        for record in self:
            record.meta_attrs_display = json.dumps(record.meta_attrs)
