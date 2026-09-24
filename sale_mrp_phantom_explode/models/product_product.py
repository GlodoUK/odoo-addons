from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_sale_mrp_phantom_explode_bom(self):
        """Return the phantom BoM flagged for sale explosion, if any."""
        self.ensure_one()
        bom = self.env["mrp.bom"].sudo()._bom_find(self, bom_type="phantom")[self]
        if bom and bom.sale_explode:
            return bom
        return self.env["mrp.bom"]

    def _get_sale_mrp_phantom_explode_components(
        self, bom, quantity, uom=None, never_attribute_values=None
    ):
        """Explode ``bom`` for ``quantity`` of this product.

        :param uom: the UoM ``quantity`` is expressed in (product UoM if None)
        :param never_attribute_values: the no_variant attribute values selected
            on the sale order line, so that "Apply on Variants" bom lines
            restricted to such values are kept/skipped correctly (same role as
            ``never_product_template_attribute_value_ids`` on stock moves)
        :return: list of ``(bom_line, qty)`` pairs for storable components,
                 with qty expressed in the bom line's UoM
        """
        self.ensure_one()
        uom = uom or self.uom_id
        factor = uom._compute_quantity(quantity, bom.product_uom_id) / bom.product_qty
        _boms, bom_sub_lines = bom.sudo().explode(
            self, factor, never_attribute_values=never_attribute_values
        )
        return [
            (bom_line, data.get("qty", 0))
            for bom_line, data in bom_sub_lines
            if bom_line.product_id.is_storable
        ]

    def sale_mrp_phantom_explode(self, quantity=None, never_attribute_value_ids=None):
        """Return the explode mode and component count in case of kit product
        flagged for sale explosion. Return False otherwise.

        Only used by the client to decide whether/how to offer the explosion;
        the explosion itself happens in the sale.order onchange.
        """
        self.ensure_one()
        bom = self._get_sale_mrp_phantom_explode_bom()
        if not bom:
            return False
        components = self._get_sale_mrp_phantom_explode_components(
            bom,
            quantity or 1,
            never_attribute_values=self.env["product.template.attribute.value"].browse(
                never_attribute_value_ids or []
            ),
        )
        if not components:
            return False
        return {"mode": bom.sale_explode, "component_count": len(components)}
