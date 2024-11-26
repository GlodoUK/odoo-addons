from odoo import fields, models


class ServerActions(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("poke", "Prompt user that record has changed")],
        ondelete={"poke": "cascade"},
    )

    def _run_action_poke_multi(self, eval_context=None):
        if eval_context is None:
            eval_context = {}

        records = eval_context.get("records") or eval_context.get("record")
        if not records:
            return False

        for record in records:
            if not record.id:
                return False

        self.env["bus.bus"]._sendone(
            "broadcast",
            "poke",
            {
                "uid": self.env.uid,
                "username": self.env.user.name,
                "model": self.model_name,
                "ids": records.ids,
            },
        )

        return False
