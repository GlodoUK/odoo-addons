import logging

from odoo import Command, api, fields, models

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    cpq_ok = fields.Boolean(related="product_id.cpq_ok")

    cpq_dynamic_bom_id = fields.Many2one(
        "cpq.dynamic.bom",
        "Configurable Bill of Materials",
        context={"active_test": False},
        index=True,
        compute="_compute_cpq_dynamic_bom_id",
        store=True,
        precompute=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id), ('type', '=', 'normal')]",
    )

    @api.depends("product_id")
    def _compute_cpq_dynamic_bom_id(self):
        for production in self:
            if not production.product_id or not production.product_id.cpq_ok:
                production.cpq_dynamic_bom_id = False
                continue

            if (
                production.cpq_dynamic_bom_id
                and production.cpq_dynamic_bom_id.product_tmpl_id
                == production.product_id.product_tmpl_id
            ):
                continue

            dyn_bom = (
                production.product_id.product_tmpl_id.cpq_dynamic_bom_ids.filtered(
                    lambda b: b.type == "normal"
                )[:1]
            )
            production.cpq_dynamic_bom_id = dyn_bom or False

    def _compute_move_raw_ids(self):
        cpq_productions = self.filtered(lambda p: p.product_id.cpq_ok)

        res = super(MrpProduction, self - cpq_productions)._compute_move_raw_ids()

        for production in self - cpq_productions:
            if production.state == "draft":
                production.move_raw_ids = [
                    Command.delete(move.id)
                    for move in production.move_raw_ids
                    if move.cpq_bom_line_id
                ]

        for production in cpq_productions:
            if production.state == "draft":
                dyn_bom = production.cpq_dynamic_bom_id

                if (
                    not dyn_bom
                    or not production.product_id
                    or production.product_qty <= 0
                ):
                    production.move_raw_ids = [Command.clear()]
                    continue

                bom_lines = dyn_bom.explode(
                    production.product_id, production.product_qty
                )

                move_by_cpq_line = {
                    move.cpq_bom_line_id.id: move
                    for move in production.move_raw_ids
                    if move.cpq_bom_line_id
                }

                list_move_raw = [Command.clear()]

                for idx, (comp_product, comp_qty, comp_uom, cpq_bom_line) in enumerate(
                    bom_lines
                ):
                    raw_vals = production._get_move_raw_values(
                        comp_product,
                        comp_qty,
                        comp_uom,
                        operation_id=False,
                        bom_line=False,
                    )

                    raw_vals.update(
                        {
                            "cpq_bom_id": dyn_bom.id,
                            "cpq_bom_line_id": cpq_bom_line.id,
                            "cpq_description": f"{production.product_id.display_name} - {idx + 1}/{len(bom_lines)}",
                        }
                    )

                    if cpq_bom_line.id in move_by_cpq_line:
                        list_move_raw.append(
                            Command.update(
                                move_by_cpq_line[cpq_bom_line.id].id, raw_vals
                            )
                        )
                    else:
                        list_move_raw.append(Command.create(raw_vals))

                production.move_raw_ids = list_move_raw

        return res

    def _compute_show_generate_bom(self):
        res = super()._compute_show_generate_bom()
        for production in self:
            if production.product_id.cpq_ok:
                production.show_generate_bom = False
        return res

    # fmt off
    # ruff: noqa: E501
    def _cpq_post_run_manufacture(self, post_production_values):
        """Mirror core _post_run_manufacture for CPQ products"""
        note_subtype_id = self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_note")
        for production, procurement in zip(self, post_production_values, strict=False):
            if group_id := procurement.values.get("production_group_id"):
                production.production_group_id.parent_ids = [Command.link(group_id)]
            orderpoint = production.orderpoint_id
            origin_production = production.move_dest_ids.raw_material_production_id
            if (
                orderpoint
                and orderpoint.create_uid.id == api.SUPERUSER_ID
                and orderpoint.trigger == "manual"
            ):
                production.message_post(
                    body=self.env._(
                        "This production order has been created from Replenishment Report."
                    ),
                    message_type="comment",
                    subtype_id=note_subtype_id,
                )
            elif orderpoint:
                production.message_post_with_source(
                    "mail.message_origin_link",
                    render_values={"self": production, "origin": orderpoint},
                    subtype_id=note_subtype_id,
                )
            elif origin_production:
                production.message_post_with_source(
                    "mail.message_origin_link",
                    render_values={"self": production, "origin": origin_production},
                    subtype_id=note_subtype_id,
                )

    # fmt on
