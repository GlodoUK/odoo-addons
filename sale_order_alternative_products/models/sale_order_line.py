from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    alternatives = fields.Many2many("product.product", compute="_compute_alternatives")

    def action_suggest_alts(self):
        self.ensure_one()
        return {
            "name": _("Available Alternatives"),  # Name You want to display on wizard
            "view_mode": "form",
            "res_model": "wizard.suggest_alternatives",
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_product_id": self.product_id.id,
                "default_alternative_ids": self.alternatives.ids,
                "default_order_line_id": self.id,
                "default_demand": self.product_uom_qty,
            },
        }

    @api.depends("product_id", "product_uom_qty")
    def _compute_alternatives(self):
        alternatives = self.env["product.product"]
        for record in self:
            if self.check_alternative_product_setting():
                record.alternatives = [(5, 0, 0)]
                if record.product_uom_qty <= 0:
                    continue
                if record.product_id.virtual_available > record.product_uom_qty:
                    continue
                if not record.product_id.stock_backup_ids:
                    continue
                alternatives |= record.product_id.stock_backup_ids.filtered(
                    lambda p: p.virtual_available > 0
                )
                record.alternatives = [(6, 0, alternatives.ids)]
            else:
                record.alternatives = [(6, 0, record.product_id.alternative_ids.ids)]

    def check_alternative_product_setting(self):
        config = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale_order_alternative_products.alternative_product")
        )

        if config == "stock":
            return True
        else:
            return False
