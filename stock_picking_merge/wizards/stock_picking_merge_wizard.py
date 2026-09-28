from odoo import api, fields, models


class StockPickingMergeWizard(models.TransientModel):
    _name = "stock.picking.merge.wizard"
    _description = "Merge Stock Pickings"

    picking_ids = fields.Many2many(
        "stock.picking",
        string="Transfer to Merge",
        readonly=True,
    )
    target_picking_id = fields.Many2one(
        "stock.picking",
        string="Target Transfter",
        compute="_compute_target_picking_id",
        store=True,
        readonly=False,
        help="All moves will be consolidated into this picking (lowest ID)."
        " The remaining pickings will be deleted.",
        domain="[('id', '=', picking_ids)]",
    )

    @api.depends("picking_ids")
    def _compute_target_picking_id(self):
        for wizard in self:
            wizard.target_picking_id = wizard.picking_ids.sorted("id")[:1]

    def action_merge(self):
        self.ensure_one()
        target = self.picking_ids._action_merge(self.target_picking_id)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Merged Picking"),
            "res_model": "stock.picking",
            "res_id": target.id,
            "view_mode": "form",
            "target": "current",
        }
