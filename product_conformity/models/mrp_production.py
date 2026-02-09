from odoo import _, api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    open_conformity_alert_count = fields.Integer(
        compute="_compute_open_conformity_alert_count",
    )

    @api.depends("product_id")
    def _compute_open_conformity_alert_count(self):
        read_group_data = self.env["product.conformity.alert"]._read_group(
            [("product_id", "in", self.product_id.ids), ("state", "=", "open")],
            ["product_id"],
            ["__count"],
        )

        mapped_data = {product_id.id: count for product_id, count in read_group_data}

        for production in self:
            production.open_conformity_alert_count = mapped_data.get(
                production.product_id.id, 0
            )

    def action_view_conformity_alerts(self):
        self.ensure_one()

        open_alert_ids = self.env["product.conformity.alert"].search(
            [
                ("product_id", "=", self.product_id.id),
                ("state", "=", "open"),
            ]
        )

        action = {
            "name": _("Conformity Alerts"),
            "res_model": "product.conformity.alert",
            "type": "ir.actions.act_window",
        }

        if len(open_alert_ids) == 1:
            action.update(
                {
                    "res_id": open_alert_ids.id,
                    "view_mode": "form",
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", open_alert_ids.ids)],
                    "view_mode": "tree,form",
                }
            )

        return action

    def button_mark_done(self):
        production_not_done_ids = self.filtered(
            lambda p: p.product_id.conformity_enabled and p.state != "done"
        )

        res = super().button_mark_done()

        self.filtered(
            lambda p: p in production_not_done_ids and p.state == "done"
        ).product_id._check_conformity_quantity()

        return res
