from odoo import api, fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _run_buy_commingled(self, procurement, rule_id):
        product_to_order = fields.first(
            procurement.product_id.commingled_ids.filtered(
                lambda c: c.product_id.active
            )
        ).product_id

        return (
            self.env["procurement.group"].Procurement(
                product_to_order,
                procurement.product_qty,
                product_to_order.uom_id,
                procurement.location_id,
                procurement.name,
                procurement.origin,
                procurement.company_id,
                procurement.values,
            ),
            rule_id,
        )

    @api.model
    def _run_buy(self, procurements):
        todo = []
        for procurement, rule in procurements:
            if procurement.product_id.commingled_ok:
                todo.append(self._run_buy_commingled(procurement, rule))
                continue

            todo.append((procurement, rule))

        return super()._run_buy(todo)
