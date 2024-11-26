from odoo import fields, models


class ServerActions(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("poke", "Prompt user that record has changed")],
        ondelete={"poke": "cascade"},
    )
    poke_msg = fields.Text(
        default="This record has been changed by another user since you opened"
        " it. The record has been automatically refreshed."
    )
    poke_refresh = fields.Boolean(default=True)
    poke_sticky = fields.Boolean(default=False)
    poke_type = fields.Selection(
        [
            ("info", "Info"),
            ("warning", "Warning"),
            ("danger", "Danger"),
            ("success", "Success"),
        ],
        default="warning",
    )

    def _run_action_poke_multi(self, eval_context=None):
        if eval_context is None:
            eval_context = {}

        records = eval_context.get("records") or eval_context.get("record")
        if not records:
            return False

        records = records.filtered(lambda r: not isinstance(r.id, models.NewId))
        if not records:
            return False

        bcast = self._run_action_poke_multi_broadcast_vals(records)

        if not bcast:
            return False

        self.env["bus.bus"]._sendone("broadcast", "poke", bcast)
        return False

    def _run_action_poke_multi_broadcast_vals(self, records):
        return {
            "uid": self.env.uid,
            "model": self.model_name,
            "ids": records.ids,
            "msg": self.poke_msg,
            "type": self.poke_type,
            "refresh": self.poke_refresh,
        }
