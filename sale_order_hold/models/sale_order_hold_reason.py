from odoo import api, fields, models
from odoo.osv import expression


class SaleOrderHoldReason(models.Model):
    _name = "sale.order.hold.reason"
    _description = "Sale Order Hold Reason"

    code = fields.Char()
    name = fields.Text(required=True)

    @api.depends("name", "code")
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            res.append((record.id, name))
        return res

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            if operator in ("=", "!="):
                domain = ["|", ("code", "=", name), ("name", operator, name)]
            else:
                domain = ["|", ("code", "=ilike", name + "%"), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )
