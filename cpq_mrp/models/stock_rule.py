from odoo import SUPERUSER_ID, _, api, fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    mrp_production_ids = fields.One2many("mrp.production", "procurement_group_id")

    @api.model
    def run(self, procurements, raise_user_error=True):
        """
        If 'run' is called on a kit which is a cpq_ok item we need to
        ensure that any BoM already exists, or is created before anything else
        in the procurement system runs. This is most critical for kits.

        We don't just override _bom_find because Odoo will call _bom_find in
        many many other places, and we dont want it creating a BoM, or any
        dynamic children unnecessarily.
        """
        procurements_without_dynamic_kit = []

        for procurement in procurements:
            product_id = procurement.product_id.with_company(procurement.company_id)
            should_explode = (
                product_id.cpq_ok and product_id.cpq_dynamic_bom_ids.type == "phantom"
            )
            if should_explode:
                bom_kit = product_id.cpq_dynamic_bom_ids
                order_qty = procurement.product_uom._compute_quantity(
                    procurement.product_qty, bom_kit.product_uom_id, round=False
                )
                qty_to_produce = order_qty / bom_kit.product_qty

                bom_lines = product_id.cpq_dynamic_bom_ids.explode(
                    product_id, qty_to_produce
                )

                for (
                    idx,
                    (
                        dyn_bom_product_id,
                        dyn_bom_product_qty,
                        dyn_uom_id,
                        cpq_bom_line_id,
                    ),
                ) in enumerate(bom_lines):
                    values = dict(**procurement.values)
                    values.update(
                        {
                            "cpq_bom_id": bom_kit.id,
                            "cpq_bom_line_id": cpq_bom_line_id.id,
                            "cpq_description": "{} - {}/{}".format(
                                product_id.display_name, idx + 1, len(bom_lines)
                            ),
                        }
                    )
                    procurements_without_dynamic_kit.append(
                        self.env["procurement.group"].Procurement(
                            dyn_bom_product_id,
                            dyn_bom_product_qty,
                            dyn_uom_id,
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


class StockRule(models.Model):
    _inherit = "stock.rule"

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

    @api.model
    def _run_manufacture(self, procurements):
        procurements_without_dynamic_bom = []

        for procurement, rule in procurements:
            product_id = procurement.product_id.with_company(procurement.company_id)
            if product_id.cpq_ok and product_id.cpq_dynamic_bom_ids.type == "normal":
                dyn_bom_id = product_id.cpq_dynamic_bom_ids
                company_id = procurement.company_id

                # create the MO as SUPERUSER because the current user may not
                # have the rights to do it (mto product launched by a sale for
                # example)

                production_values = rule._prepare_mo_vals(
                    *procurement, self.env["mrp.bom"]
                )
                production_values.update(
                    {
                        "consumption": dyn_bom_id.consumption,
                        "picking_type_id": dyn_bom_id.picking_type_id.id,
                    }
                )

                production = (
                    self.env["mrp.production"]
                    .with_user(SUPERUSER_ID)
                    .sudo()
                    .with_company(company_id)
                    .create(production_values)
                )
                bom_lines = dyn_bom_id.explode(product_id, procurement.product_qty)

                production_raw_move_values = []
                for (
                    idx,
                    (
                        component_product_id,
                        component_qty,
                        component_uom_id,
                        cpq_bom_line_id,
                    ),
                ) in enumerate(bom_lines):
                    raw_move_values = production._get_move_raw_values(
                        component_product_id,
                        component_qty,
                        component_uom_id,
                        operation_id=False,
                        bom_line=False,
                    )
                    raw_move_values.update(
                        {
                            "cpq_description": "{} - {}/{}".format(
                                product_id.display_name, idx + 1, len(bom_lines)
                            ),
                            "cpq_bom_id": dyn_bom_id.id,
                            "cpq_bom_line_id": cpq_bom_line_id.id,
                        }
                    )
                    production_raw_move_values.append(raw_move_values)

                # we need to create the raw moves by hand
                self.env["stock.move"].sudo().create(production_raw_move_values)
                self.env["stock.move"].sudo().create(
                    production._get_moves_finished_values()
                )
                production._create_workorder()
                production.filtered(
                    self._should_auto_confirm_procurement_mo
                ).action_confirm()

                origin_production = (
                    production.move_dest_ids
                    and production.move_dest_ids[0].raw_material_production_id
                    or False
                )
                orderpoint = production.orderpoint_id
                if (
                    orderpoint
                    and orderpoint.create_uid.id == SUPERUSER_ID
                    and orderpoint.trigger == "manual"
                ):
                    production.message_post(
                        body=_(
                            "This production order has been created "
                            "from Replenishment Report."
                        ),
                        message_type="comment",
                        subtype_xmlid="mail.mt_note",
                    )
                elif orderpoint:
                    production.message_post_with_view(
                        "mail.message_origin_link",
                        values={"self": production, "origin": orderpoint},
                        subtype_id=self.env.ref("mail.mt_note").id,
                    )
                elif origin_production:
                    production.message_post_with_view(
                        "mail.message_origin_link",
                        values={"self": production, "origin": origin_production},
                        subtype_id=self.env.ref("mail.mt_note").id,
                    )
            else:
                procurements_without_dynamic_bom.append((procurement, rule))

        return super()._run_manufacture(procurements_without_dynamic_bom)
