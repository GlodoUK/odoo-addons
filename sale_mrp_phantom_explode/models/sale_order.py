from odoo import Command, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def _onchange_order_line_sale_mrp_phantom_explode(self):
        """
        Replace kit lines flagged for explosion by their component lines.

        Mirrors how combos are implemented in the core ``sale`` module, by using a
        special trigger field (``sale_mrp_phantom_explode_requested``).

        Why an onchange method, when they're discouraged?
         * Building the component lines client-side is unpleasant
         * it results in a slow "ticking" as each line is visibly added
         * and error prone as it relies on directly filling in missing field values
           client side

        Unlike the combo code we resequence *every* line: lines routinely
        share the default sequence, which would leave the component lines'
        position ambiguous; unique sequences keep the client-side sort
        deterministic, with the components taking the kit line's place.
        """
        if not any(self.order_line.mapped("sale_mrp_phantom_explode_requested")):
            return
        commands = []
        sequence = 0
        for line in self.order_line:
            if line.sale_mrp_phantom_explode_requested:
                # Clear the trigger to avoid applying the changes again on a
                # later onchange pass (same as combo's selected_combo_items).
                line.sale_mrp_phantom_explode_requested = False
                bom = line.product_id._get_sale_mrp_phantom_explode_bom()
                components = (
                    line.product_id._get_sale_mrp_phantom_explode_components(
                        bom,
                        line.product_uom_qty,
                        uom=line.product_uom_id,
                        never_attribute_values=(
                            line.product_no_variant_attribute_value_ids
                        ),
                    )
                    if bom
                    else []
                )
                if components:
                    commands.append(
                        Command.create(
                            line._prepare_sale_mrp_phantom_explode_section_values(
                                sequence=sequence
                            )
                        )
                    )
                    sequence += 1
                    for bom_line, quantity in components:
                        commands.append(
                            Command.create(
                                line._prepare_sale_mrp_phantom_explode_line_values(
                                    bom_line, quantity, sequence=sequence
                                )
                            )
                        )
                        sequence += 1
                    # Command.delete works on unsaved lines too (NewId), as
                    # relied upon by the combo code for its linked lines.
                    commands.append(Command.delete(line.id))
                    continue
            line.sequence = sequence
            sequence += 1
        if commands:
            self.order_line = commands
