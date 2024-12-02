import ast

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_repr


class DynamicBom(models.Model):
    _name = "cpq.dynamic.bom"
    _inherit = ["mail.thread"]
    _description = "Configurable Dynamic BoM"
    _order = "id asc"

    active = fields.Boolean(default=True, index=True)
    code = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        index=True,
    )
    type = fields.Selection(
        [
            ("phantom", "Kit"),
            ("normal", "Manufacture"),
        ],
        default="phantom",
        required=True,
        index=True,
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        index=True,
        domain="[('cpq_ok', '=', True)]",
        string="Product",
    )
    product_tmpl_uom_category_id = fields.Many2one(
        related="product_tmpl_id.uom_id.category_id"
    )
    bom_line_ids = fields.One2many(
        "cpq.dynamic.bom.line", "bom_id", context={"active_test": False}
    )
    product_qty = fields.Float(default=1.0, required=True)
    product_uom_id = fields.Many2one("uom.uom", required=True)

    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Operation Type",
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        check_company=True,
        help="When a procurement has a ‘produce’ route with a operation type"
        " set, it will try to create a Manufacturing Order for that product"
        " using a BoM of the same operation type. That allows to define stock"
        " rules which trigger different manufacturing orders with different BoMs.",
    )
    consumption = fields.Selection(
        [
            ("flexible", "Allowed"),
            ("warning", "Allowed with warning"),
            ("strict", "Blocked"),
        ],
        help="Defines if you can consume more or less components than the "
        " quantity defined on the BoM:\n"
        "  * Allowed: allowed for all manufacturing users.\n"
        "  * Allowed with warning: allowed for all manufacturing users with"
        " summary of consumption differences when closing the manufacturing order.\n"
        "  * Blocked: only a manager can close a manufacturing order when the"
        " BoM consumption is not respected.",
        default="warning",
        string="Flexible Consumption",
        required=True,
    )

    possible_product_template_attribute_value_ids = fields.Many2many(
        "product.template.attribute.value",
        compute="_compute_possible_product_template_attribute_value_ids",
    )

    workcenter_id = fields.Many2one(
        "mrp.workcenter",
        string="Work Center",
        help="Work Center to be used for manufacturing orders with this BoM.",
    )

    _sql_constraints = [
        (
            "qty_positive",
            "check (product_qty > 0)",
            "The quantity to produce must be positive!",
        ),
    ]

    def init(self):
        # we want a unique constraint only if the bom is active
        self.env.cr.execute(
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS
            cpq_dynamic_bom_unique ON {self._table}
            (product_tmpl_id)
            WHERE active is true
            """
        )

    @api.depends("code", "product_tmpl_id.display_name")
    def _compute_display_name(self):
        for bom in self:
            bom.display_name = "{}{}".format(
                bom.code and f"[{bom.code}] " or "",
                bom.product_tmpl_id.display_name,
            )

    @api.constrains("product_tmpl_id")
    def _ensure_product_tmpl_id_cpq_ok(self):
        if not all(self.mapped("product_tmpl_id.cpq_ok")):
            raise ValidationError(
                _("Product Template must be enabled as configurable"))

    @api.constrains("type", "picking_type_id")
    def _ensure_manufacture_has_picking_type_id(self):
        if not self.user_has_groups("stock.group_adv_location"):
            return

        if self.filtered(lambda b: b.type == "normal" and not b.picking_type_id):
            raise ValidationError(
                _("Manufactured dynamic BoMs must have an operation type set")
            )

    @api.constrains("type", "workcenter_id")
    def _ensure_manufacture_has_workcenter_id(self):
        if not self.user_has_groups("mrp.group_mrp_user"):
            return

        if self.filtered(lambda b: b.type == "normal" and not b.workcenter_id):
            raise ValidationError(
                _("Manufactured dynamic BoMs must have a work center set")
            )

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl_id(self):
        res = {}
        if self.product_tmpl_id:
            self.product_uom_id = self.product_tmpl_id.uom_id
            if self._origin and self._origin.product_tmpl_id != self.product_tmpl_id:
                self.code = False

            existing_standard_boms = (
                self.env["mrp.bom"]
                .sudo()
                .search_count([("product_tmpl_id", "=", self.product_tmpl_id.id)])
            )
            if existing_standard_boms > 0:
                res["warning"] = {
                    "title": _("Standard BoMs Exist"),
                    "message": _(
                        "There are already %d standard BoMs for this product!"
                        " These should be archived, or you will experience"
                        " inconsistent BoM handling!"
                    )
                    % (existing_standard_boms),
                }
        return res

    @api.onchange("product_uom_id")
    def onchange_product_uom_id(self):
        res = {}
        if not self.product_uom_id or not self.product_tmpl_id:
            return
        if self.product_uom_id.category_id != self.product_tmpl_id.uom_id.category_id:
            self.product_uom_id = self.product_tmpl_id.uom_id
            res["warning"] = {
                "title": _("Warning"),
                "message": _(
                    "The Product Unit of Measure you chose has a different"
                    " category than in the product form."
                ),
            }
        return res

    def explode(self, product_id, quantity):
        self.ensure_one()

        if product_id.product_tmpl_id != self.product_tmpl_id:
            raise ValidationError(
                _("The product variant is not related to this bom template")
            )

        bom_lines = []

        for bom_line in self.bom_line_ids:
            sub_bom_lines = bom_line._explode_line(product_id, quantity)
            if sub_bom_lines:
                bom_lines.extend(sub_bom_lines)

        # Add work center information to the exploded lines
        for line in bom_lines:
            line[3].workcenter_id = self.workcenter_id

        return bom_lines

    def _get_exploded_qty_dict(self, product_id):
        # Explode a BoM and convert the component UoM into the 'reference' UoM.
        # Combine the same product.product together.
        # This is a utility method for cpq_sale_mrp, mostly

        components = {}
        bom_lines = self.explode(product_id, 1.0)

        for product, qty, uom, _cpq_bom_line_id in bom_lines:
            if components.get(product, False):
                if uom != components[product]["uom"]:
                    from_uom = uom
                    to_uom = components[product]["uom"]
                    qty = from_uom._compute_quantity(qty, to_uom)
                components[product]["qty"] += qty
            else:
                # To be in the uom reference of the product
                to_uom = product.uom_id
                if uom.id != to_uom.id:
                    from_uom = uom
                    qty = from_uom._compute_quantity(qty, to_uom)
                components[product] = {"qty": qty, "uom": to_uom}
        return components

    @api.depends(
        "product_tmpl_id.attribute_line_ids.value_ids",
        "product_tmpl_id.attribute_line_ids.attribute_id",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids.ptav_active",
    )
    def _compute_possible_product_template_attribute_value_ids(self):
        for bom in self:
            # Formatting has been disabled here because black and flake8 have an
            # argument about whats "best".
            # Black says 1 line.
            # flake8 says line too long.
            # I agree with flake8, its illegible.

            # fmt: off
            bom.possible_product_template_attribute_value_ids = (
                bom
                .product_tmpl_id
                .valid_product_template_attribute_line_ids
                ._without_no_variant_attributes()
                .product_template_value_ids
                ._only_active()
            )
            # fmt: on


class DynamicBomLine(models.Model):
    _name = "cpq.dynamic.bom.line"
    _description = "Configurable Dynamic BoM Line"
    _order = "sequence asc, id asc"

    sequence = fields.Integer(default=16)
    name = fields.Char(compute="_compute_name", store=False)
    active = fields.Boolean(related="bom_id.active", store=True, index=True)
    bom_id = fields.Many2one("cpq.dynamic.bom", required=True, index=True)
    bom_product_tmpl_id = fields.Many2one(related="bom_id.product_tmpl_id")
    company_id = fields.Many2one(related="bom_id.company_id", store=True)
    condition_type = fields.Selection(
        [
            ("always", "Always"),
            ("domain", "Domain"),
            ("ptav", "Apply on Variants"),
        ],
        required=True,
        default="always",
    )
    condition_domain = fields.Char()

    condition_possible_ptav_ids = fields.Many2many(
        related="bom_id.possible_product_template_attribute_value_ids"
    )

    condition_ptav_ids = fields.Many2many(
        "product.template.attribute.value",
        domain="[('id', 'in', condition_possible_ptav_ids)]",
    )
    component_type = fields.Selection(
        [
            ("variant", "Variant"),
            ("template", "Template"),
        ],
        required=True,
        default="variant",
    )
    component_product_id = fields.Many2one("product.product")
    component_product_tmpl_id = fields.Many2one(
        "product.template",
    )
    component_product_tmpl_id_cpq_ok = fields.Boolean(
        related="component_product_tmpl_id.cpq_ok"
    )
    component_product_tmpl_ptav_passthru_ids = fields.Many2many(
        "product.template.attribute.value",
        compute="_compute_component_product_tmpl_ptav_passthru_ids",
    )
    quantity_type = fields.Selection(
        [
            ("fixed", "Fixed"),
            ("ptav_custom_id", "From Configurable Custom Value"),
        ],
        required=True,
        default="fixed",
    )
    quantity_fixed = fields.Float(default=1)
    quantity_ptav_custom_id = fields.Many2one(
        "product.template.attribute.value",
        domain="["
        "('product_tmpl_id', '=', bom_product_tmpl_id),"
        "('cpq_allow_dynamic_bom_quantity', '=', True),"
        "]",
    )
    display_quantity = fields.Char(compute="_compute_display_quantity")
    uom_id = fields.Many2one(
        "uom.uom",
        required=True,
        string="Unit of Measure",
    )

    @api.depends("product_tmpl_id", "product_tmpl_id.cpq_ok")
    def _ensure_product_tmpl_id_cpq_ok(self):
        for record in self:
            if not record.product_tmpl_id.cpq_ok:
                raise ValidationError(_("Product must be configurable"))

    @api.constrains("uom_id", "component_type")
    def _ensure_valid_uom(self):
        for record in self:
            if not record.uom_id:
                raise ValidationError(_("UoM not present"))

            if (
                record.component_type == "variant"
                and record.component_product_id.uom_id.category_id
                != record.uom_id.category_id
            ):
                raise ValidationError(_("UoM not of the same category"))

            if (
                record.component_type == "template"
                and record.component_product_tmpl_id.uom_id.category_id
                != record.uom_id.category_id
            ):
                raise ValidationError(_("UoM not of the same category"))

    @api.onchange("component_type", "uom_id")
    def onchange_uom_id(self):
        res = {}
        if not self.uom_id:
            return

        if self.component_type == "variant" and self.component_product_id:
            if self.uom_id.category_id != self.component_product_id.uom_id.category_id:
                self.uom_id = self.component_product_id.uom_id.id
                res["warning"] = {
                    "title": _("Warning"),
                    "message": _(
                        "The Product Unit of Measure you chose has a different"
                        " category than in the product form."
                    ),
                }

        if self.component_type == "template" and self.component_product_tmpl_id:
            if (
                self.uom_id.category_id
                != self.component_product_tmpl_id.uom_id.category_id
            ):
                self.uom_id = self.component_product_tmpl_id.uom_id.id
                res["warning"] = {
                    "title": _("Warning"),
                    "message": _(
                        "The Product Unit of Measure you chose has a different"
                        " category than in the product form."
                    ),
                }

        return res

    @api.onchange("component_type", "component_product_tmpl_id", "component_product_id")
    def _onchange_component_type(self):
        if self.component_type == "variant" and self.component_product_id:
            self.uom_id = self.component_product_id.uom_id

        if self.component_type == "template" and self.component_product_tmpl_id:
            self.uom_id = self.component_product_tmpl_id.uom_id

    @api.depends("component_type", "component_product_tmpl_id", "component_product_id")
    def _compute_name(self):
        for record in self:
            if record.component_type == "variant" and record.component_product_id:
                record.name = record.component_product_id.display_name
                continue

            if record.component_type == "template" and record.component_product_tmpl_id:
                record.name = record.component_product_tmpl_id.display_name
                continue

            record.name = False

    @api.depends("bom_product_tmpl_id", "component_type", "component_product_tmpl_id")
    def _compute_component_product_tmpl_ptav_passthru_ids(self):
        for record in self:
            if (
                not record.bom_product_tmpl_id
                or record.component_type != "template"
                or not record.component_product_tmpl_id
            ):
                record.component_product_tmpl_ptav_passthru_ids = False
                continue

            # build attrs for *this* line and *this* current_product_tmpl_id
            passthru_ptav_ids = self.env["product.template.attribute.value"]
            current_product_tmpl_id = record.component_product_tmpl_id

            # fmt: off
            valid_product_tmpl_ptav_ids = (
                record
                .bom_product_tmpl_id
                .valid_product_template_attribute_line_ids
                .mapped("product_template_value_ids")
            )
            # fmt: on

            for ptav_id in valid_product_tmpl_ptav_ids:
                # find a matching ptav for the child product
                passthru_ptav_ids |= self.env[
                    "product.template.attribute.value"
                ].search(
                    [
                        ("product_tmpl_id", "=", current_product_tmpl_id.id),
                        ("attribute_id", "=", ptav_id.attribute_id.id),
                        (
                            "product_attribute_value_id",
                            "=",
                            ptav_id.product_attribute_value_id.id,
                        ),
                        ("attribute_line_id.active", "=", True),
                    ]
                )

            record.component_product_tmpl_ptav_passthru_ids = passthru_ptav_ids

    @api.depends("quantity_type", "quantity_ptav_custom_id", "quantity_fixed", "uom_id")
    def _compute_display_quantity(self):
        for record in self:
            if not record.uom_id:
                record.display_quantity = False

            if record.quantity_type == "fixed":
                # XXX(Karl): This is lazy. Lets do it properly.
                precision = len(
                    str(record.uom_id.rounding or "0.01").split(".")[1])

                record.display_quantity = float_repr(
                    record.quantity_fixed, precision)
                continue

            if record.quantity_type == "ptav_custom_id":
                record.display_quantity = _("Dynamic from %(attribute_name)s") % {
                    "attribute_name": record.quantity_ptav_custom_id.display_name,
                }

    def _skip_bom_line(self, parent_product_id):
        if self.condition_type == "always":
            return False

        if self.condition_type == "domain":
            domain = ast.literal_eval(self.condition_domain)
            return not bool(parent_product_id.filtered_domain(domain))

        if self.condition_type == "ptav":
            return not parent_product_id._match_all_variant_values(
                self.condition_ptav_ids
            )

        return True

    def _explode_line(self, parent_product_id, parent_quantity):
        self.ensure_one()

        if self._skip_bom_line(parent_product_id):
            return

        method_explode_quantity_name = f"_explode_quantity_{self.quantity_type}"
        quantity = getattr(self, method_explode_quantity_name)(
            parent_product_id, parent_quantity
        )

        if float_is_zero(quantity, precision_rounding=self.uom_id.rounding):
            return

        method_explode_product_name = f"_explode_get_product_from_{self.component_type}"
        product_id = getattr(self, method_explode_product_name)(
            parent_product_id)

        if product_id.cpq_ok and product_id.product_tmpl_id.cpq_dynamic_bom_ids:
            # have we got a dynamic bom inside of a dynamic bom?
            return product_id.product_tmpl_id.cpq_dynamic_bom_ids.explode(
                product_id, quantity
            )

        standard_kit_bom_id = (
            self.env["mrp.bom"]
            ._bom_find(product_id, bom_type="phantom")
            .get(product_id)
        )
        if standard_kit_bom_id and not product_id.cpq_ok:
            # we've got a standard mrp.bom kit inside of this item.
            # we should explode that and add that to our output.
            (_boms_done, lines_done) = standard_kit_bom_id.explode(
                product_id, quantity)

            standard_kit_bom_res = []

            for mrp_bom_line_id, mrp_bom_line_dict in lines_done:
                # Adjust the quantities to the quantities of a procurement if
                # its UoM isn't the same as the one of the quant and the
                # parameter 'propagate_uom' is not set.
                bom_line_uom = mrp_bom_line_id.product_uom_id
                quant_uom = mrp_bom_line_id.product_id.uom_id
                component_qty, procurement_uom = bom_line_uom._adjust_uom_quantities(
                    mrp_bom_line_dict["qty"], quant_uom
                )

                standard_kit_bom_res.append(
                    (
                        mrp_bom_line_id.product_id,
                        component_qty,
                        procurement_uom,
                        self,
                    )
                )

            return standard_kit_bom_res

        # adjust the quantities to the quantities of a procurement if its UoM isn't the
        # same as the one of the quant and the parameter 'propagate_uom' is not set.
        component_qty, procurement_uom = self.uom_id._adjust_uom_quantities(
            quantity, product_id.uom_id
        )

        return [
            (product_id, component_qty, procurement_uom, self),
        ]

    def _explode_get_product_from_variant(self, parent_product_id):
        return self.component_product_id

    def _explode_get_product_from_template(self, parent_product_id):
        passthru_ptav_ids = self.env["product.template.attribute.value"]
        passthru_custom_dict = {}

        for ptav_id in parent_product_id.product_template_attribute_value_ids:
            # find a matching ptav for the child product
            passthru_id = self.env["product.template.attribute.value"].search(
                [
                    ("product_tmpl_id", "=", self.component_product_tmpl_id.id),
                    ("attribute_id", "=", ptav_id.attribute_id.id),
                    (
                        "product_attribute_value_id",
                        "=",
                        ptav_id.product_attribute_value_id.id,
                    ),
                    ("attribute_line_id.active", "=", True),
                ]
            )

            if not passthru_id:
                continue

            passthru_ptav_ids |= passthru_id

            if passthru_id.is_custom:
                custom_value_id = parent_product_id.cpq_custom_value_ids.filtered(
                    lambda v: v.ptav_id == ptav_id  # noqa: B023
                )
                if custom_value_id:
                    passthru_custom_dict.update(
                        {passthru_id: custom_value_id.custom_value}
                    )

        if self.component_product_tmpl_id.cpq_ok:
            # generate a variant
            return self.component_product_tmpl_id._cpq_get_create_variant(
                passthru_ptav_ids, passthru_custom_dict
            )

        # find a standard product.template that matchesz
        return self.component_product_tmpl_id._get_variant_for_combination(
            passthru_ptav_ids
        )

    def _explode_quantity_fixed(self, parent_product_id, parent_quantity):
        return parent_quantity * self.quantity_fixed

    def _explode_quantity_ptav_custom_id(self, parent_product_id, parent_quantity):
        custom_id = parent_product_id.cpq_custom_value_ids.filtered(
            lambda v: self.quantity_ptav_custom_id == v.ptav_id
        )
        if not custom_id:
            raise ValidationError(
                _("Could not find custom value to propagate as quantity!")
            )

        return parent_quantity * float(custom_id.custom_value)
