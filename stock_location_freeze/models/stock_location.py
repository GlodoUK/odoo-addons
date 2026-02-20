from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockLocation(models.Model):
    _inherit = "stock.location"

    frozen = fields.Boolean(default=False, string="Is Frozen?", readonly=True)
    frozen_parent_path = fields.Boolean(
        compute="_compute_frozen_parent_path",
        store=True,
        recursive=True,
        string="Is Directly or Parent Frozen?",
    )
    frozen_by_ancestor = fields.Boolean(
        compute="_compute_frozen_by_ancestor", store=False
    )
    freeze_reason_id = fields.Many2one("stock.location.freeze.reason", readonly=True)
    freeze_uid = fields.Many2one("res.users", readonly=True, string="Frozen By")
    freeze_date = fields.Datetime(readonly=True)
    unfreeze_uid = fields.Many2one("res.users", readonly=True, string="Unfrozen By")
    unfreeze_date = fields.Datetime(readonly=True)

    @api.depends("name", "location_id.frozen_parent_path", "frozen", "parent_path")
    def _compute_frozen_parent_path(self):
        for location in self:
            location.frozen_parent_path = (
                location.frozen or location.location_id.frozen_parent_path
            )

    @api.depends("frozen_parent_path", "frozen")
    def _compute_frozen_by_ancestor(self):
        for location in self:
            location.frozen_by_ancestor = (
                not location.frozen and location.frozen_parent_path
            )

    def _ensure_not_frozen(self):
        if self.env.context.get("stock_location_freeze_skip", False):
            return

        for record in self:
            if record.frozen_parent_path:
                origin_id = self.env["stock.location"].search(
                    [("location_id", "parent_of", record.id), ("frozen", "=", True)],
                    order="parent_path asc",
                    limit=1,
                )

                raise UserError(
                    _(
                        "Location '%(location)s' is frozen. "
                        "Please check the configuration at '%(origin)s'."
                    )
                    % {
                        "location": record.display_name,
                        "origin": origin_id.display_name,
                    }
                )

    def _check_can_be_used(self, product, quantity=0, package=None, location_qty=0):
        self.ensure_one()
        # XXX: if the location is frozen then it's not valid for putaway rules at this
        # time
        if self.frozen_parent_path and not self.env.context.get(
            "stock_location_freeze_skip", False
        ):
            return False
        return super()._check_can_be_used(
            product, quantity=quantity, package=package, location_qty=location_qty
        )

    def action_freeze(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_location_freeze.action_stock_location_freeze"
        )
        action["context"] = {"default_location_id": self.id}
        return action

    def action_unfreeze(self):
        self.ensure_one()
        self.write(
            {
                "frozen": False,
                "unfreeze_uid": self.env.uid,
                "unfreeze_date": fields.Datetime.now(),
            }
        )
