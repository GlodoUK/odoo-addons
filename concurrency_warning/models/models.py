from odoo import api, fields, models


class ServerActions(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("poke", "Prompt user that record has changed")],
        ondelete={"poke": "cascade"},
    )

    @api.model
    def run_action_poke_multi(self, action, eval_context={}):
        # Use a set rather than a list because it prevents duplicate ids when
        # calling union()
        record_set = set()
        newly_created = False

        record = eval_context.get("record", None)
        if record:
            record_set = record_set.union(record.ids)
            if record.exists() and record.create_date == record.write_date:
                newly_created = True

        records = eval_context.get("records", None)
        if records:
            record_set = record_set.union(records.ids)

        self.env["bus.bus"].sendone(
            "poke",
            {
                "uid": self.env.uid,
                "username": self.env.user.name,
                "model": action.model_name,
                "ids": list(record_set),
                "create": newly_created,
            },
        )
