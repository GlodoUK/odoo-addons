from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    product_tmpl_id = fields.Many2one(
        related="product_id.product_tmpl_id",
        store=True,
        index=True
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    orderpoint_ids = fields.One2many(
        "stock.warehouse.orderpoint",
        "product_tmpl_id",
    )

    orderpoint_count = fields.Integer(compute="_compute_orderpoint_count")

    @api.multi
    def _compute_orderpoint_count(self):
        for record in self:
            record.orderpoint_count = len(record.orderpoint_ids)

    def action_orderpoint_link(self):
        view = self.env.ref("stock.action_orderpoint_form").read()[0]

        view["domain"] = [("id", "in", self.orderpoint_ids.ids)]
        view["display_name"] = "Reordering Rules"

        return view


class ProductProduct(models.Model):
    _inherit = "product.product"

    orderpoint_count = fields.Integer(compute="_compute_orderpoint_count")

    @api.multi
    def _compute_orderpoint_count(self):
        for record in self:
            record.orderpoint_count = len(record.orderpoint_ids)

    def action_orderpoint_link(self):
        view = self.env.ref("stock.action_orderpoint_form").read()[0]

        view["domain"] = [("id", "in", self.orderpoint_ids.ids)]
        view["display_name"] = "Reordering Rules"

        return view
