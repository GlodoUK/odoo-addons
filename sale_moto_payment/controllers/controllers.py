from werkzeug.exceptions import Forbidden, NotFound

from odoo import Command, http
from odoo.http import request
from odoo.tools import is_html_empty

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers.portal import PaymentPortal


class SaleInstantPaymentController(PaymentPortal):
    @http.route(
        "/sale_moto_payment/pay/<int:order_id>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def moto_payment(self, order_id, **kwargs):
        order = request.env["sale.order"].browse(order_id)
        if not order.exists() or order.state not in ("draft", "sent"):
            raise NotFound()

        partner = order.partner_invoice_id
        amount = order.amount_total - order.amount_paid
        currency = order.currency_id
        company = order.company_id

        availability_report = {}
        providers_sudo = (
            request.env["payment.provider"]
            .sudo()
            ._get_compatible_providers(
                company.id,
                partner.id,
                amount,
                currency_id=currency.id,
                sale_order_id=order.id,
                report=availability_report,
            )
        )
        payment_methods_sudo = (
            request.env["payment.method"]
            .sudo()
            ._get_compatible_payment_methods(
                providers_sudo.ids,
                partner.id,
                currency_id=currency.id,
                sale_order_id=order.id,
                report=availability_report,
            )
        )
        tokens_sudo = (
            request.env["payment.token"]
            .sudo()
            ._get_available_tokens(providers_sudo.ids, partner.id)
        )
        vals = {
            "order": order,
            "reference_prefix": payment_utils.singularize_reference_prefix(
                prefix="SIP"
            ),
            "amount": amount,
            "currency": currency,
            "partner_id": partner.id,
            "providers_sudo": providers_sudo,
            "payment_methods_sudo": payment_methods_sudo,
            "tokens_sudo": tokens_sudo,
            "availability_report": availability_report,
            "transaction_route": f"/sale_moto_payment/transaction/{order_id}",
            "landing_route": f"/sale_moto_payment/pay/{order_id}/return",
            "access_token": payment_utils.generate_access_token(
                partner.id, amount, currency.id
            ),
            "show_tokenize_input_mapping": self._compute_show_tokenize_input_mapping(
                providers_sudo, sale_order_id=order.id
            ),
            "is_html_empty": is_html_empty,
        }

        return request.render(
            "sale_moto_payment.payment_page",
            vals,
        )

    @http.route(
        "/sale_moto_payment/transaction/<int:order_id>",
        type="jsonrpc",
        auth="user",
    )
    def moto_payment_transaction(self, order_id, access_token, **kwargs):
        order = request.env["sale.order"].browse(order_id)
        if not order.exists():
            raise NotFound()

        amount = float(kwargs.get("amount", 0))
        partner_id = order.partner_invoice_id.id
        currency_id = order.currency_id.id

        if not payment_utils.check_access_token(
            access_token, partner_id, amount, currency_id
        ):
            raise Forbidden()

        self._validate_transaction_kwargs(kwargs)
        kwargs.update({"partner_id": partner_id, "currency_id": currency_id})

        tx_sudo = self._create_transaction(
            custom_create_values={
                "sale_order_ids": [Command.set([order_id])],
                "is_moto": True,
            },
            **kwargs,
        )
        self._update_landing_route(tx_sudo, access_token)
        return tx_sudo._get_processing_values()

    @http.route(
        "/sale_moto_payment/pay/<int:order_id>/return",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def moto_payment_return(self, order_id, **kwargs):
        return request.render(
            "sale_moto_payment.payment_return",
            {"order_id": order_id},
        )
