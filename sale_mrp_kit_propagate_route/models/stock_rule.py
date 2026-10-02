from collections import defaultdict

from odoo import api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def run(self, procurements, raise_user_error=True):
        """mrp's run() replaces a kit's procurement with one per component
        before any rule is chosen, so each component follows its own routes
        and one kit can ship from several places. For a kit sold on a sale
        order whose BoM has "On Sale Components Follow Kit Route", hand mrp the
        procurement with the routes every component should take; mrp copies
        its values onto each of them."""
        return super().run(
            self._kit_propagate_route(procurements),
            raise_user_error=raise_user_error,
        )

    @api.model
    def _kit_propagate_route_applies(self, procurement):
        # Routes already there (the line's, or the carrier's) were chosen for
        # the order, and reach the components as they are.
        return procurement.values.get("sale_line_id") and not procurement.values.get(
            "route_ids"
        )

    @api.model
    def _kit_propagate_route(self, procurements):
        product_ids_by_company = defaultdict(set)
        for procurement in procurements:
            if self._kit_propagate_route_applies(procurement):
                product_ids_by_company[procurement.company_id].add(
                    procurement.product_id.id
                )
        if not product_ids_by_company:
            return procurements
        kits_by_company = {
            company: self.env["mrp.bom"]._bom_find(
                self.env["product.product"].browse(product_ids),
                company_id=company.id,
                bom_type="phantom",
            )
            for company, product_ids in product_ids_by_company.items()
        }

        result = []
        for procurement in procurements:
            kit = self._kit_propagate_route_applies(procurement) and kits_by_company[
                procurement.company_id
            ].get(procurement.product_id)
            if kit and kit.sale_kit_propagate_route:
                routes = self._kit_propagate_route_routes(procurement)
                if routes:
                    procurement = procurement._replace(
                        values=dict(procurement.values, route_ids=routes)
                    )
            result.append(procurement)
        return result

    @api.model
    def _kit_propagate_route_routes(self, procurement):
        """The kit's own routes, or the warehouse's delivery route when it has
        none, so the components ship from the warehouse rather than wherever
        their own routes would send them."""
        product = procurement.product_id
        routes = product.route_ids | product.categ_id.total_route_ids
        if not routes:
            warehouse = procurement.values.get("warehouse_id")
            routes = warehouse.delivery_route_id if warehouse else routes
        return routes
