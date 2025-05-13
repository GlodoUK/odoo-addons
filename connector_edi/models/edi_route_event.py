from odoo import api, fields, models


class EdiBackendRouteEvent(models.Model):
    _name = "edi.route.event"
    _description = "EDI Message Route Model Event"

    name = fields.Char(
        "Event",
        required=True,
    )

    res_model_id = fields.Many2one(
        "ir.model",
        "Document Model",
        ondelete="cascade",
    )

    res_model = fields.Char(
        "Document Model Name",
        related="res_model_id.model",
        store=True,
    )

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True,
        compute_sudo=True,
    )

    @api.depends("res_model_id")
    def _compute_display_name(self):
        res = super()._compute_display_name()

        for event in self.filtered_domain([("res_model_id", "=", True)]):
            event.display_name = f"{event.res_model}: {event.name}"

        return res
