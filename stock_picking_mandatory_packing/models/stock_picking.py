from odoo import models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _sanity_check(self, separate_pickings=True):
        res = super()._sanity_check(separate_pickings=separate_pickings)
        for picking in self.filtered(lambda x: x.picking_type_id.must_be_packed):
            move_lines_without_package = picking.move_line_ids.filtered(
                lambda x: not x.result_package_id
            )
            if move_lines_without_package:
                raise UserError(
                    self.env._(
                        "The following move lines have not been packaged: %(line)s",
                        line=", ".join(
                            move_lines_without_package.mapped("display_name")
                        ),
                    )
                )
        return res
