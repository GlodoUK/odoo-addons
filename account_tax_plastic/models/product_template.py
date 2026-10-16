from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plastic_weight = fields.Float(
        digits="Stock Weight",
        help="Weight of plastic per unit in the system weight unit. Converted to kg"
        " when calculating plastic tax.",
    )

    @api.model
    def _plastic_weight_to_kg(self, weight):
        # Plastic tax rates are per kg, but weights are held in the system unit.
        weight_uom = self._get_weight_uom_id_from_ir_config_parameter()
        kg = self.env.ref("uom.product_uom_kgm")
        if not weight or weight_uom == kg:
            return weight
        return weight_uom._compute_quantity(weight, kg, round=False)
