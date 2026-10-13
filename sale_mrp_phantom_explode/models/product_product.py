from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_sale_mrp_phantom_explode_components(
        self, quantity, uom=None, never_attribute_values=None, company=None
    ):
        """Explode this product's kit BoM for ``quantity``.

        :param uom: the UoM ``quantity`` is expressed in (product UoM if None)
        :param never_attribute_values: the no_variant attribute values selected
            on the sale order line, so that "Apply on Variants" bom lines
            restricted to such values are kept/skipped correctly (same role as
            ``never_product_template_attribute_value_ids`` on stock moves)
        :return: list of ``(bom_line, qty)`` pairs for storable components,
                 with qty expressed in the bom line's UoM; empty if not a kit
        """
        self.ensure_one()
        bom = (
            self.env["mrp.bom"]
            .sudo()
            ._bom_find(
                self, bom_type="phantom", company_id=company.id if company else False
            )[self]
        )
        if not bom:
            return []
        uom = uom or self.uom_id
        factor = uom._compute_quantity(quantity, bom.product_uom_id) / bom.product_qty
        _boms, bom_sub_lines = bom.explode(
            self, factor, never_attribute_values=never_attribute_values
        )
        return [
            (bom_line, data.get("qty", 0))
            for bom_line, data in bom_sub_lines
            if bom_line.product_id.is_storable
        ]
