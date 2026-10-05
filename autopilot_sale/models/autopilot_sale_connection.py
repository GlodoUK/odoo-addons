from odoo import fields, models


class AutopilotSaleConnection(models.Model):
    """A Sale EDI endpoint (see ``autopilot.fsspec.mixin``), shared by any
    number of backends. Sales managers maintain them, so the storage options
    are opened up to them too."""

    _name = "autopilot_sale.connection"
    _inherit = ["autopilot.fsspec.mixin"]
    _description = "Sale EDI Connection"

    storage_options = fields.Text(
        groups="base.group_system,sales_team.group_sale_manager"
    )
