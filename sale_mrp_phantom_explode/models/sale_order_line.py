from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    can_sale_mrp_phantom_explode = fields.Boolean(
        related="product_id.sale_mrp_phantom_explode_ok",
        help="Fast path to determine if we can offer a phantom explode",
    )
    # Transient UI trigger, never stored: when the client sets it, the
    # sale.order onchange above replaces this kit line by its component lines.
    sale_mrp_phantom_explode_requested = fields.Boolean(store=False)

    def action_sale_mrp_phantom_explode(self):
        """Explode kit lines into their component lines.

        The sale order equivalent of ``stock.move.action_explode``: each line
        whose product resolves to a phantom BoM flagged for sale explosion is
        replaced by a section line named after the kit followed by one line
        per storable component; every other line is left untouched.

        Intended for programmatic / background order entry. The BoM's
        ask/always mode is deliberately ignored: explosion is the caller's
        responsibility, so if you call this it explodes.

        :return: the resulting lines (untouched lines + new component lines)
        """
        lines_to_return = self.env["sale.order.line"]
        lines_to_unlink = self.env["sale.order.line"]
        new_lines_vals = []
        for line in self:
            if line.display_type or line.state not in ("draft", "sent"):
                lines_to_return |= line
                continue
            bom = line.product_id._get_sale_mrp_phantom_explode_bom()
            if not bom:
                lines_to_return |= line
                continue
            components = line.product_id._get_sale_mrp_phantom_explode_components(
                bom, line.product_uom_qty, uom=line.product_uom_id
            )
            if not components:
                lines_to_return |= line
                continue
            new_lines_vals.append(
                {
                    "order_id": line.order_id.id,
                    **line._prepare_sale_mrp_phantom_explode_section_values(),
                }
            )
            for bom_line, quantity in components:
                new_lines_vals.append(
                    {
                        "order_id": line.order_id.id,
                        **line._prepare_sale_mrp_phantom_explode_line_values(
                            bom_line, quantity
                        ),
                    }
                )
            lines_to_unlink |= line
        if new_lines_vals:
            lines_to_return |= self.create(new_lines_vals)
        lines_to_unlink.unlink()
        return lines_to_return

    def _prepare_sale_mrp_phantom_explode_line_values(
        self, bom_line, quantity, sequence=None
    ):
        self.ensure_one()
        return {
            "product_id": bom_line.product_id.id,
            "product_uom_id": bom_line.product_uom_id.id,
            "product_uom_qty": quantity,
            "sequence": self.sequence if sequence is None else sequence,
        }

    def _prepare_sale_mrp_phantom_explode_section_values(self, sequence=None):
        """Section line housing the exploded components, named after the kit.

        Sections own the lines below them positionally (parent_id is computed
        from sequence order), so creating this right before the components is
        all it takes.
        """
        self.ensure_one()
        return {
            "display_type": "line_section",
            "name": self.product_id.name,
            "sequence": self.sequence if sequence is None else sequence,
        }
