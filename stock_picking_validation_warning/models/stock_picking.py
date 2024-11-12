from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_partner_for_warning(self):
        partner_id = self.partner_id

        if partner_id.picking_warn in (False, "no-message") and partner_id.parent_id:
            partner_id = partner_id.parent_id

        return partner_id

    def button_validate(self):
        self.ensure_one()

        partner_id = self._get_partner_for_warning()
        has_warning = (
            partner_id.picking_warn in ("warning", "block")
            and partner_id.picking_warn_msg
        )

        if not has_warning or self.env.context.get("skip_picking_warning_check", False):
            return super().button_validate()

        view = self.env.ref(
            "stock_picking_validation_warning.view_stock_picking_warning"
        )
        wiz = self.env["stock.picking.warning"].create({"picking_id": self.id})
        return {
            "name": ("Warning for %s") % self.partner_id.name,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "stock.picking.warning",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": wiz.id,
            "context": self.env.context,
        }
