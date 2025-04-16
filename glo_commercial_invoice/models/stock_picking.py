from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_commercial_invoice(self):
        # check if all move lines have a hs code
        for move_line in self.move_line_ids:
            if not move_line.intrastat_code_id or not move_line.intrastat_country_id:
                raise UserError(
                    _("Please set HS code and Country of Manufacture on all products.")
                )

        return self.env.ref(
            "glo_commercial_invoice.action_report_commercial_invoice"
        ).report_action(self)
