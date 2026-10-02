from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    glodo_instance_ids = fields.One2many("glodo.instance", "partner_id", readonly=True)

    def action_view_instance(self):
        """View instance for this contact."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Instance - %(name)s", name=self.name),
            "res_model": "glodo.instance",
            "view_mode": "form",
            "domain": [("partner_id", "=", self.id)],
            "res_id": self.glodo_instance_ids[0].id
            if len(self.glodo_instance_ids) == 1
            else False,
        }
