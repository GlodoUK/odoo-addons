from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    glodo_instance_ids = fields.One2many("glodo.instance", "partner_id", readonly=True)

    def action_view_instance(self):
        """View instances for this contact."""
        self.ensure_one()

        instances = self.glodo_instance_ids
        action = {
            "type": "ir.actions.act_window",
            "name": self.env._("Instance - %(name)s", name=self.name),
            "res_model": "glodo.instance",
            "domain": [("id", "in", instances.ids)],
        }
        if len(instances) == 1:
            action.update(view_mode="form", res_id=instances.id)
        else:
            action["view_mode"] = "list,form"
        return action
