from odoo import models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    # Based on upstream _compute_scrap_location_id
    def _compute_scrap_location_id(self):
        res = super()._compute_scrap_location_id()

        groups = self.env["stock.location"]._read_group(
            [
                ("company_id", "in", self.company_id.ids),
                ("usage", "=", "inventory"),
                ("scrap_location", "=", True),
            ],
            ["company_id"],
            ["id:min"],
        )

        locations_per_company = {
            company.id: stock_warehouse_id for company, stock_warehouse_id in groups
        }

        # Keep upstream's location when the company has no flagged scrap location
        for scrap in self:
            if scrap.company_id:
                scrap.scrap_location_id = locations_per_company.get(
                    scrap.company_id.id, scrap.scrap_location_id
                )

        return res
