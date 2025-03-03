from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round


class ProductCommingled(models.Model):
    _inherit = "product.commingled"

    qty_available = fields.Float(related="product_id.qty_available")
    virtual_available = fields.Float(related="product_id.virtual_available")
    free_qty = fields.Float(related="product_id.free_qty")
    incoming_qty = fields.Float(related="product_id.incoming_qty")
    outgoing_qty = fields.Float(related="product_id.outgoing_qty")


COMMINGLED_POLICY = [
    ("deplete", "Prioritise Depleting Stock"),
    ("strict", "Exact Sequence"),
]
COMMINGLED_DEFAULT = "deplete"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    commingled_policy = fields.Selection(
        COMMINGLED_POLICY,
        default=COMMINGLED_DEFAULT,
        required=True,
        compute="_compute_commingled_policy",
        inverse="_inverse_commingled_policy",
    )
    commingled_prefer_homogenous = fields.Boolean(
        default=True,
        compute="_compute_commingled_prefer_homogenous",
        inverse="_inverse_commingled_prefer_homogenous",
    )

    @api.depends("product_variant_ids.commingled_policy")
    def _compute_commingled_policy(self):
        for record in self:
            if len(record.product_variant_ids) == 1:
                record.commingled_policy = record.product_variant_ids.commingled_policy
            else:
                record.commingled_policy = COMMINGLED_DEFAULT

    def _inverse_commingled_policy(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.product_variant_ids.commingled_policy = p.commingled_policy

    @api.depends("product_variant_ids.commingled_prefer_homogenous")
    def _compute_commingled_prefer_homogenous(self):
        for record in self:
            if len(record.product_variant_ids) == 1:
                record.commingled_prefer_homogenous = (
                    record.product_variant_ids.commingled_prefer_homogenous
                )
            else:
                record.commingled_prefer_homogenous = True

    def _inverse_commingled_prefer_homogenous(self):
        for p in self:
            if len(p.product_variant_ids) == 1:
                p.product_variant_ids.commingled_prefer_homogenous = (
                    p.commingled_prefer_homogenous
                )


class ProductProduct(models.Model):
    _inherit = "product.product"

    commingled_policy = fields.Selection(
        COMMINGLED_POLICY,
        default=COMMINGLED_DEFAULT,
        required=True,
    )
    commingled_prefer_homogenous = fields.Boolean(default=True)

    def _explode_commingled_needs(self, qty, location_id=None):
        self.ensure_one()
        if not self.commingled_ok:
            raise UserError(_("Product is not commingled"))

        if not self.commingled_ids:
            raise UserError(
                _("Product %s has no commingled products") % (self.display_name)
            )

        bom_lines = []

        for current_line in self.commingled_ids:
            line_quantity = qty
            available_line_quantity = qty

            if location_id:
                # get the amount in stock at this location, in the product's
                # default UoM, if we've been passed a location, otherwise we
                # have to assume we have the full stock, since we have no way of
                # checking...
                available_line_quantity = current_line.product_id.with_context(
                    location=location_id.id
                ).free_qty

            # convert it to our line UoM
            available_line_quantity = current_line.product_id.uom_id._compute_quantity(
                available_line_quantity, self.uom_id
            )

            bom_lines.append(
                (
                    current_line,
                    {
                        "available_quantity": available_line_quantity,
                        "needed_quantity": line_quantity,
                    },
                )
            )

        return bom_lines

    def _explode_commingled_sorted(self, bom_needs):
        self.ensure_one()

        if self.commingled_policy == "strict":
            bom_needs.sort(key=lambda x: x[0].sequence)

        if self.commingled_policy == "deplete":
            bom_needs.sort(key=lambda n: n[1]["available_quantity"])

        return bom_needs

    def _explode_commingled(self, quantity, location_id=None):
        self.ensure_one()

        bom_needs = self._explode_commingled_needs(quantity, location_id)

        if not bom_needs:
            raise UserError(_("No commingled products found!"))

        # used later
        highest_bom_needs = bom_needs[:1]

        # sort the bom_needs by the policy
        bom_needs = self._explode_commingled_sorted(bom_needs)

        if self.commingled_prefer_homogenous:
            # Can we completely fulfill an order with a single item? If so, prefer
            # that.
            complete_products = list(
                filter(
                    lambda line_data: line_data[1]["available_quantity"]
                    >= line_data[1]["needed_quantity"],
                    bom_needs,
                )
            )

            if complete_products:
                bom_line, line_data = next(iter(complete_products))
                return [
                    (
                        bom_line,
                        {
                            "qty": line_data["needed_quantity"],
                            "uom_qty": line_data["needed_quantity"],
                        },
                    )
                ]

        # Can't get a complete item, use the highest priority (top of the
        # list), take as much as we can and then continue.
        return_lines = []
        quantity_left = quantity

        for bom_line, line_data in bom_needs:
            if quantity_left <= 0:
                break

            qty = min(line_data["available_quantity"], quantity_left)

            if qty > 0:
                quantity_left -= qty

                return_lines.append(
                    (
                        bom_line,
                        {
                            "qty": qty,
                            "uom_qty": qty,
                        },
                    )
                )

        # If we've got any left, take it from the highest priority
        if quantity_left > 0:
            bom_line, line_data = highest_bom_needs[0]

            # round up any halves or odd numbers we get
            return_lines.append(
                (
                    bom_line,
                    {
                        "qty": float_round(
                            quantity_left,
                            precision_rounding=bom_line.product_id.uom_id.rounding,
                            rounding_method="UP",
                        ),
                        "uom_qty": quantity_left,
                    },
                )
            )

        return return_lines
