from odoo import exceptions
from odoo.http import request, route

from odoo.addons.sale_stock.controllers.portal import SaleStockPortal


class DriftworksSaleStockPortal(SaleStockPortal):
    # Hard Override https://github.com/odoo/odoo/blob/16.0/addons/sale_stock/controllers/portal.py#L24
    @route()
    def portal_my_picking_report(self, picking_id, access_token=None, **kw):
        try:
            picking_sudo = self._stock_picking_check_access(
                picking_id,
                access_token=access_token,
            )
        except exceptions.AccessError:
            return request.redirect("/my")

        return self._show_report(
            model=picking_sudo,
            report_type="pdf",
            report_ref="stock.action_report_delivery",
            download=True,
        )
