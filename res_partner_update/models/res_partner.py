from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_update_ids = fields.One2many(
        "res.partner.update",
        "partner_id",
    )

    partner_update_count = fields.Integer(compute="_compute_partner_update_count")

    def _compute_partner_update_count(self):
        if not self.ids:
            self.partner_update_count = 0
            return

        res_partner_update_data = self.env["res.partner.update"]._read_group(
            [("partner_id", "in", self.ids)],
            ["partner_id"],
            ["__count"],
        )

        count_data = {partner.id: count for partner, count in res_partner_update_data}

        for partner in self:
            partner.partner_update_count = count_data.get(partner.id, 0)

    def action_view_res_partner_update(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Partner Updates"),
            "res_model": "res.partner.update",
            "view_mode": "list,form",
            "context": {"default_partner_id": self.id},
        }
