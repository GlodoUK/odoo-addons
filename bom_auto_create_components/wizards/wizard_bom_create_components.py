# Copyright 2022 ForgeFlow S.L. <https://forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from itertools import product

from odoo import api, fields, models


class WizardSimpleCreateVariant(models.TransientModel):
    _name = "wizard.bom.create.components"
    _description = "Create BoM Components Wizard"

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template", string="Template", readonly=True
    )
    variants_to_create = fields.Integer(compute="_compute_variants_to_create")
    line_ids = fields.One2many(
        comodel_name="wizard.bom.create.components.line",
        inverse_name="wizard_id",
        string="Lines",
        required=False,
        readonly=False,
    )
    component_product_id = fields.Many2one(
        comodel_name="product.template",
        required=True,
        domain="[('id', '!=', product_tmpl_id)]",
    )

    @api.depends(
        "product_tmpl_id",
        "line_ids.selected_value_ids",
        "component_product_id",
    )
    def _compute_variants_to_create(self):
        for rec in self:
            combinations = rec._get_combinations()
            rec.variants_to_create = len(combinations)

    def _get_combinations(self):
        self.ensure_one()
        selected_items = [
            line.selected_value_ids.ids
            for line in self.line_ids
            if line.selected_value_ids
        ]
        return list(selected_items and product(*selected_items))

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        bom = self.env["mrp.bom"].browse(self.env.context.get("active_id"))
        values["product_tmpl_id"] = bom.product_tmpl_id.id
        return values

    @api.onchange("product_tmpl_id", "component_product_id")
    def _onchange_product_tmpl(self):
        line_model = self.env["wizard.bom.create.components.line"]
        if self.product_tmpl_id and self.component_product_id:
            lines = line_model.browse()
            pending_variants = self.product_tmpl_id.attribute_line_ids.filtered(
                lambda line: line.attribute_id
                in self.component_product_id.attribute_line_ids.mapped("attribute_id")
            )
            pending_values = pending_variants.mapped("value_ids").filtered(
                lambda value: value
                in self.component_product_id.attribute_line_ids.value_ids
            )
            for line_data in [
                {
                    "attribute_id": attribute_line.attribute_id.id,
                    "required": attribute_line.required,
                    "attribute_value_ids": [
                        (
                            6,
                            0,
                            [
                                int(v_id)
                                for v_id in attribute_line.value_ids.filtered(
                                    lambda line: line.id in pending_values.ids
                                ).ids
                            ],
                        )
                    ],
                }
                for attribute_line in pending_variants
            ]:
                lines |= line_model.new(line_data)
            self.line_ids = lines

    def fetch_variant_from_combination(self, product_template, combination_ids):
        all_variants = product_template.product_variant_ids
        existing_variants = {
            variant.product_template_attribute_value_ids: variant
            for variant in all_variants
        }
        combination = self.env["product.template.attribute.value"]
        for value in product_template.valid_product_template_attribute_line_ids.mapped(
            "product_template_value_ids"
        ):
            if value.product_attribute_value_id.id in combination_ids:
                combination |= value
        is_combination_possible = product_template._is_combination_possible_by_config(
            combination, ignore_no_variant=False
        )
        if not is_combination_possible:
            return False
        if combination in existing_variants:
            return existing_variants[combination]
        return False

    def action_create_components(self):
        self.action_create_variants()
        bom = self.env["mrp.bom"].browse(self.env.context.get("active_id"))
        # Create Bom Component Lines for all attribute value combinations
        for combination in self._get_combinations():
            component_variant = self.fetch_variant_from_combination(
                self.component_product_id, combination
            )
            for component_variant_id in component_variant:
                bom_line = self.env["mrp.bom.line"].create(
                    {
                        "product_id": component_variant_id.id,
                        "product_qty": 1.0,
                        "bom_id": bom.id,
                    }
                )
                bom_line._onchange_set_apply_variant()
        return {"type": "ir.actions.act_window_close"}

    def action_create_variants(self):
        """Create variant of product based on selected attributes values in wizard"""
        product_model = self.env["product.product"]
        attribute_value_model = self.env["product.template.attribute.value"]
        product_tmpl_ids = self.product_tmpl_id + self.component_product_id
        for product_tmpl in product_tmpl_ids:
            current_variants_to_create = []
            current_variants_to_activate = product_model.browse()
            all_variants = product_tmpl.with_context(
                active_test=False
            ).product_variant_ids.sorted(lambda p: (p.active, -p.id))
            existing_variants = {
                variant.product_template_attribute_value_ids: variant
                for variant in all_variants
            }
            for combination_ids in self._get_combinations():
                combination = attribute_value_model.browse()
                for (
                    value
                ) in product_tmpl.valid_product_template_attribute_line_ids.mapped(
                    "product_template_value_ids"
                ):
                    if value.product_attribute_value_id.id in combination_ids:
                        combination |= value
                is_combination_possible = (
                    product_tmpl._is_combination_possible_by_config(
                        combination, ignore_no_variant=False
                    )
                )
                if not is_combination_possible:
                    continue
                if combination in existing_variants:
                    current_variants_to_activate += existing_variants[combination]
                elif (
                    existing_variants
                    and len(existing_variants) == 1
                    and not all_variants.product_template_attribute_value_ids
                ):
                    all_variants.write(
                        {
                            "product_template_attribute_value_ids": [
                                (6, 0, combination.ids)
                            ]
                        }
                    )
                else:
                    current_variants_to_create.append(
                        {
                            "product_tmpl_id": product_tmpl.id,
                            "product_template_attribute_value_ids": [
                                (6, 0, combination.ids)
                            ],
                            "active": product_tmpl.active,
                        }
                    )
            if current_variants_to_activate:
                current_variants_to_activate.write({"active": True})
            if current_variants_to_create:
                product_model.create(current_variants_to_create)


class WizardCreateVariantLine(models.TransientModel):
    _name = "wizard.bom.create.components.line"
    _description = "Create BoM Components Wizard Line"

    wizard_id = fields.Many2one(
        comodel_name="wizard.bom.create.components",
        string="Wizard",
        required=False,
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute", string="Attribute", required=False
    )
    attribute_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="wizard_bom_create_components_line_value_rel",
        column1="wizard_line_id",
        column2="value_id",
        string="Matching Values",
        readonly=True,
    )
    selected_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="wizard_bom_create_components_line_selected_value_rel",
        column1="wizard_line_id",
        column2="value_id",
        string="Selected Values",
    )
    required = fields.Boolean(
        string="Required?",
        required=False,
    )
