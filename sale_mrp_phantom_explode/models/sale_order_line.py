from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_is_kit = fields.Boolean(related="product_id.is_kits")

    def action_sale_mrp_phantom_explode(self):
        """Explode kit lines into their component lines.

        The sale order equivalent of ``stock.move.action_explode``: each kit
        line is replaced, in place, by a section line named after the kit
        followed by one line per storable component. Other lines are left
        untouched.
        """
        lines_to_unlink = self.browse()
        new_lines_vals = []
        for order in self.order_id:
            if order.state not in ("draft", "sent"):
                continue
            # Renumber the whole order: lines routinely share a sequence, which
            # would leave the components' position ambiguous.
            sequence = 0
            for line in order.order_line:
                components = (
                    line in self
                    and not line.display_type
                    and line.product_id._get_sale_mrp_phantom_explode_components(
                        line.product_uom_qty,
                        uom=line.product_uom_id,
                        never_attribute_values=(
                            line.product_no_variant_attribute_value_ids
                        ),
                        company=line.company_id,
                    )
                )
                if not components:
                    line.sequence = sequence
                    sequence += 1
                    continue
                new_lines_vals.append(
                    {
                        "order_id": order.id,
                        "display_type": "line_section",
                        "name": line.product_id.name,
                        "sequence": sequence,
                    }
                )
                sequence += 1
                for bom_line, quantity in components:
                    new_lines_vals.append(
                        {
                            "order_id": order.id,
                            "product_id": bom_line.product_id.id,
                            "product_uom_id": bom_line.product_uom_id.id,
                            "product_uom_qty": quantity,
                            "sequence": sequence,
                        }
                    )
                    sequence += 1
                lines_to_unlink |= line
        # Unlink last: the kit line must stay readable until the order is done.
        self.env["sale.order.line"].create(new_lines_vals)
        lines_to_unlink.unlink()
        return True
