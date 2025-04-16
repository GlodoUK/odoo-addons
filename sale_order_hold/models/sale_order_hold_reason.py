from odoo import api, fields, models
from odoo.osv import expression


class SaleOrderHoldReason(models.Model):
    _name = "sale.order.hold.reason"
    _description = "Sale Order Hold Reason"

    name = fields.Text(
        required=True,
    )

    code = fields.Char(
        copy=False,
    )

    @api.depends("code")
    def _compute_display_name(self):
        res = super()._compute_display_name()

        for reason in self.filtered(lambda r: r.code):
            reason.display_name = f"[{reason.code}] {reason.name}"

        return res

    @api.model
    def _search_display_name(self, operator, value):
        name = value or ""

        if operator in ("=", "!="):
            domain = ["|", ("code", "=", name.split(" ")[0]), ("name", operator, name)]

        else:
            domain = [
                "|",
                ("code", "=like", name.split(" ")[0] + "%"),
                ("name", operator, name),
            ]

        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = ["&", "!"] + domain[1:]

        return domain
