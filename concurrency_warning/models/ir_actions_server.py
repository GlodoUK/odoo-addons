from odoo import api, fields, models


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("poke", "Prompt user that record has changed")],
        ondelete={"poke": "cascade"},
    )
    poke_msg = fields.Text(
        default="This record has been changed by another user since you opened it.",
        string="Message",
    )
    poke_refresh = fields.Boolean(default=True, string="Automatically refresh")
    poke_sticky = fields.Boolean(default=False, string="Sticky notification")
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

        records = records.filtered(lambda r: not isinstance(r.id, api.NewId))
        if not records:
            return False

        for record in records:
            self.env["bus.bus"]._sendone(
                "poke",
                "poke/live_update",
                {
                    "type": self.poke_type,
                    "message": self.poke_msg,
                    "refresh": self.poke_refresh,
                    "resId": record.id,
                    "resModel": record._name,
                    "userId": self.env.uid,
                    "sticky": self.poke_sticky,
                },
            )
        return False
