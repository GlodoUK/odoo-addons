from odoo import api, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _update_available_quantity(
        self,
        product_id,
        location_id,
        quantity,
        lot_id=None,
        package_id=None,
        owner_id=None,
        in_date=None,
    ):
        location_id.with_context(
            stock_location_freeze_skip=self.env.context.get(
                "stock_location_freeze_skip"
            )
        )._ensure_not_frozen()
        return super()._update_available_quantity(
            product_id, location_id, quantity, lot_id, package_id, owner_id, in_date
        )

    @api.model
    def _update_reserved_quantity(
        self,
        product_id,
        location_id,
        quantity,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        location_id.with_context(
            stock_location_freeze_skip=self.env.context.get(
                "stock_location_freeze_skip"
            )
        )._ensure_not_frozen()
        return super(
            StockQuant, self.with_context(stock_location_freeze_gather=True)
        )._update_reserved_quantity(
            product_id, location_id, quantity, lot_id, package_id, owner_id, strict
        )

    def _gather(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        res = super()._gather(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

        if self.env.context.get(
            "stock_location_freeze_gather", False
        ) and not self.env.context.get("stock_location_freeze_skip", False):
            res = res.filtered(lambda x: not x.location_id.frozen_parent_path)

        return res
