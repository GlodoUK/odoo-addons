from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockImmediateTransfer(models.TransientModel):
    _name = "stock.picking.warning"
    _description = "Stock Picking Warning"

    picking_id = fields.Many2one(
        "stock.picking",
    )
    msg = fields.Text(compute="_compute_msg")
    should_block = fields.Boolean(
        compute="_compute_should_block",
    )

    @api.depends("picking_id")
    def _compute_should_block(self):
        for rec in self:
            partner_id = rec.picking_id._get_partner_for_warning()
            rec.should_block = (
                partner_id.picking_warn == "block" and partner_id.picking_warn_msg
            )

    @api.depends("picking_id")
    def _compute_msg(self):
        for rec in self:
            partner_id = rec.picking_id._get_partner_for_warning()
            rec.msg = partner_id.picking_warn_msg

    def process(self):
        if self.should_block:
            raise UserError(
                _(
                    "You can not process the picking because "
                    "the partner has set the option to block the picking."
                )
            )

        return self.with_context(
            skip_picking_warning_check=True
        ).picking_id.button_validate()
