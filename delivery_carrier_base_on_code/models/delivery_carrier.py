from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("base_on_code", "Based on Code")],
        ondelete={"base_on_code": "set default"},
    )

    code = fields.Text(
        "Python Code",
    )

    @api.constrains("code", "delivery_type")
    def _check_python_code(self):
        carrier_ids = self.sudo().filtered(
            lambda c: c.delivery_type == "base_on_code" and c.code
        )

        for carrier in carrier_ids:
            msg = test_python_expr(expr=carrier.code.strip(), mode="exec")
            if msg:
                raise ValidationError(msg)

    # ruff: noqa: E501
    def base_on_code_rate_shipment(self, order):
        carrier_id = self._match_address(order.partner_shipping_id)

        if not carrier_id:
            return {
                "success": False,
                "price": 0.0,
                "error_message": self.env._(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }

        try:
            price_unit = self._get_base_on_code_price(order)

        except UserError as e:
            return {
                "success": False,
                "price": 0.0,
                "error_message": e.args[0],
                "warning_message": False,
            }

        price_unit = self._compute_currency(order, price_unit, "company_to_pricelist")

        return {
            "success": True,
            "price": price_unit,
            "error_message": False,
            "warning_message": False,
        }

    def base_on_code_send_shipping(self, pickings):
        res = []

        for p in pickings:
            carrier = self._match_address(p.partner_id)
            if not carrier:
                raise ValidationError(self.env._("There is no matching delivery rule."))
            res = res + [
                {
                    "exact_price": (
                        p.carrier_id._get_base_on_code_price(p.sale_id)
                        if p.sale_id
                        else 0.0
                    ),
                    "tracking_number": False,
                }
            ]
        return res

    @api.model
    def _get_base_on_code_eval_context(self, order):
        eval_context = self.env["ir.actions.actions"]._get_eval_context()
        eval_context.update(order=order, result=None)
        return eval_context

    def _get_base_on_code_price(self, order):
        eval_context = self._get_base_on_code_eval_context(order)
        safe_eval(self.sudo().code or "", eval_context, mode="exec")
        price = eval_context.get("result")
        if price is None:
            raise UserError(self.env._("Not available for current order"))
        return float(price)
