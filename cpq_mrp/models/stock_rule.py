from collections import defaultdict

from odoo import SUPERUSER_ID, api, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def run(self, procurements, raise_user_error=True):
        """If 'run' is called on a kit which is a cpq_ok item we need to
        ensure that any BoM already exists, or is created before anything else
        in the procurement system runs. This is most critical for kits.

        We don't just override _bom_find because Odoo will call _bom_find in
        many many other places, and we dont want it creating a BoM, or any
        dynamic children unnecessarily.
        """
        procurements_without_dynamic_kit = []

        for procurement in procurements:
            product_id = procurement.product_id.with_company(procurement.company_id)
            bom_kit = product_id.cpq_ok and product_id.cpq_dynamic_bom_ids.filtered(
                lambda b: b.type == "phantom"
            )
            if bom_kit:
                bom_kit = bom_kit[:1]
                order_qty = procurement.product_uom._compute_quantity(
                    procurement.product_qty, bom_kit.product_uom_id, round=False
                )
                qty_to_produce = order_qty / bom_kit.product_qty
                bom_lines = bom_kit.explode(product_id, qty_to_produce)

                for idx, (comp_product, comp_qty, comp_uom, cpq_bom_line) in enumerate(
                    bom_lines
                ):
                    values = dict(
                        procurement.values,
                        cpq_bom_id=bom_kit.id,
                        cpq_bom_line_id=cpq_bom_line.id,
                        cpq_description=f"{product_id.display_name} - {idx + 1}/{len(bom_lines)}",  # noqa: E501
                    )
                    procurements_without_dynamic_kit.append(
                        self.env["stock.rule"].Procurement(
                            comp_product,
                            comp_qty,
                            comp_uom,
                            procurement.location_id,
                            procurement.name,
                            procurement.origin,
                            procurement.company_id,
                            values,
                        )
                    )
            else:
                procurements_without_dynamic_kit.append(procurement)

        return super().run(
            procurements_without_dynamic_kit, raise_user_error=raise_user_error
        )

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        move_values = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if values.get("cpq_bom_line_id"):
            move_values["cpq_bom_line_id"] = values["cpq_bom_line_id"]
        if values.get("cpq_bom_id"):
            move_values["cpq_bom_id"] = values["cpq_bom_id"]
        if values.get("cpq_description"):
            move_values["cpq_description"] = values["cpq_description"]
        return move_values

    # fmt: off
    @api.model
    def _run_manufacture(self, procurements):
        procurements_without_dynamic_bom = []
        cpq_productions_by_company = defaultdict(lambda: defaultdict(list))

        for procurement, rule in procurements:
            product_id = procurement.product_id.with_company(procurement.company_id)
            if not (product_id.cpq_ok and product_id.cpq_dynamic_bom_ids.type == "normal"):  # noqa: E501
                procurements_without_dynamic_bom.append((procurement, rule))
                continue

            if procurement.product_uom.compare(procurement.product_qty, 0) <= 0:
                continue

            dyn_bom_id = product_id.cpq_dynamic_bom_ids[:1]

            production_values = rule._prepare_mo_vals(
                *procurement, self.env["mrp.bom"]
            )
            picking_type = dyn_bom_id.picking_type_id or rule.picking_type_id
            production_values.update({
                "consumption": dyn_bom_id.consumption,
                "picking_type_id": picking_type.id,
                "location_src_id": picking_type.default_location_src_id.id,
                "cpq_dynamic_bom_id": dyn_bom_id.id,
            })

            cpq_productions_by_company[procurement.company_id.id]["values"].append(production_values)
            cpq_productions_by_company[procurement.company_id.id]["procurements"].append(procurement)

        for company_id, data in cpq_productions_by_company.items():
            # Raw moves are created by _compute_move_raw_ids which
            # detects cpq_dynamic_bom_id and explodes the dynamic BOM.
            # Finished moves are handled by _compute_move_finished_ids.
            productions = (
                self.env["mrp.production"]
                .with_user(SUPERUSER_ID)
                .sudo()
                .with_company(company_id)
                .create(data["values"])
            )

            for mo in productions:
                if self._should_auto_confirm_procurement_mo(mo):
                    mo.action_confirm()

            productions._cpq_post_run_manufacture(data["procurements"])

        return super()._run_manufacture(procurements_without_dynamic_bom)
    # fmt: on

    def _filter_warehouse_routes(self, product, warehouses, route):
        if any(rule.action == "manufacture" for rule in route.rule_ids):
            has_dynamic_bom = (
                product.cpq_ok
                and product.product_tmpl_id.cpq_dynamic_bom_ids.filtered(
                    lambda b: b.type == "normal"
                )
            )
            if has_dynamic_bom:
                # Bypass MRP's standard-BoM gate: CPQ products use dynamic BoMs.
                return route
        return super()._filter_warehouse_routes(product, warehouses, route)


class StockRoute(models.Model):
    _inherit = "stock.route"

    def _is_valid_resupply_route_for_product(self, product):
        if any(rule.action == "manufacture" for rule in self.rule_ids):
            has_dynamic_bom = (
                product.cpq_ok
                and product.product_tmpl_id.cpq_dynamic_bom_ids.filtered(
                    lambda b: b.type == "normal"
                )
            )
            if has_dynamic_bom:
                return True
        return super()._is_valid_resupply_route_for_product(product)
