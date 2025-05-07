from werkzeug.exceptions import NotFound

from odoo import exceptions
from odoo.http import request, route

from odoo.addons.sale_stock.controllers.portal import SaleStockPortal


class SaleStockPortal(SaleStockPortal):
    # Hard Override https://github.com/odoo/odoo/blob/18.0/addons/sale_stock/controllers/portal.py#L24 # noqa: E501
    @route()
    def portal_my_picking_report(self, picking_id, access_token=None, **kw):
        try:
            picking_sudo = self._stock_picking_check_access(
                picking_id,
                access_token=access_token,
            )
        except (exceptions.AccessError, exceptions.MissingError):
            return NotFound()

        pdf = (
            request.env["ir.actions.report"]
            .sudo()
            ._render_qweb_pdf("stock.action_report_delivery", [picking_sudo.id])[0]
        )

        filename = picking_sudo.name

        pdfhttpheaders = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", f"attachment; filename={filename}.pdf"),
        ]

        return request.make_response(pdf, headers=pdfhttpheaders)

    # Hard Override https://github.com/odoo/odoo/blob/18.0/addons/sale_stock/controllers/portal.py#L41 # noqa: E501
    @route()
    def portal_my_picking_return_report(self, picking_id, access_token=None, **kw):
        try:
            picking_sudo = self._stock_picking_check_access(
                picking_id,
                access_token=access_token,
            )
        except (exceptions.AccessError, exceptions.MissingError):
            return NotFound()

        pdf = (
            request.env["ir.actions.report"]
            .sudo()
            ._render_qweb_pdf("stock.return_label_report", [picking_sudo.id])[0]
        )

        filename = f"{picking_sudo.name} Return"

        pdfhttpheaders = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", f"attachment; filename={filename}.pdf"),
        ]

        return request.make_response(pdf, headers=pdfhttpheaders)
