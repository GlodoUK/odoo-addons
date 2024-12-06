# Copyright 2022 ForgeFlow S.L. <https://forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from itertools import product

from odoo import api, fields, models


class WizardSimpleCreateVariant(models.TransientModel):
    _name = "wizard.simple.create.variant"
    _description = "Simple Create Variant Wizard"

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template", string="Template", readonly=True
    )
    variants_to_create = fields.Integer(compute="_compute_variants_to_create")
    line_ids = fields.One2many(
        comodel_name="wizard.simple.create.variant.line",
        inverse_name="wizard_id",
        string="Lines",
        required=False,
    )

    @api.depends(
        "product_tmpl_id",
        "line_ids.selected_value_ids",
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
        values["product_tmpl_id"] = self.env.context.get("active_id")
        return values

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl(self):
        line_model = self.env["wizard.simple.create.variant.line"]
        if self.product_tmpl_id:
            lines = line_model.browse()
            pending_variants = self.product_tmpl_id.attribute_line_ids
            pending_variants = pending_variants.filtered(
                lambda tmpl_att_line: tmpl_att_line.attribute_id.display_type != "multi"
            )
            for line_data in [
                {
                    "attribute_id": attribute_line.attribute_id.id,
                    "required": attribute_line.required,
                    "attribute_value_ids": [
                        (6, 0, [int(v_id) for v_id in attribute_line.value_ids.ids])
                    ],
                }
                for attribute_line in pending_variants
            ]:
                lines |= line_model.new(line_data)
            self.line_ids = lines

    def action_create_variants(self):
        """Create variant of product based on selected attributes values in wizard"""
        product_model = self.env["product.product"]
        attribute_value_model = self.env["product.template.attribute.value"]
        current_variants_to_create = []
        current_variants_to_activate = product_model.browse()
        variants_to_show = product_model.browse()
        product_tmpl = self.product_tmpl_id
        all_variants = product_tmpl.with_context(
            active_test=False
        ).product_variant_ids.sorted(lambda p: (p.active, -p.id))
        existing_variants = {
            variant.product_template_attribute_value_ids: variant
            for variant in all_variants
        }
        for combination_ids in self._get_combinations():
            combination = attribute_value_model.browse()
            for value in product_tmpl.valid_product_template_attribute_line_ids.mapped(
                "product_template_value_ids"
            ):
                if value.product_attribute_value_id.id in combination_ids:
                    combination |= value
            is_combination_possible = product_tmpl._is_combination_possible_by_config(
                combination, ignore_no_variant=False
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
                variants_to_show += all_variants
                all_variants.write(
                    {"product_template_attribute_value_ids": [(6, 0, combination.ids)]}
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
            variants_to_show |= current_variants_to_activate
            current_variants_to_activate.write({"active": True})
        if current_variants_to_create:
            variants_to_show |= product_model.create(current_variants_to_create)
        if variants_to_show:
            action = self.env.ref("product.product_variant_action").read()[0]
            action.update(
                {
                    "domain": [("id", "in", variants_to_show.ids)],
                    "context": {
                        "search_default_product_tmpl_id": [product_tmpl.id],
                        "default_product_tmpl_id": product_tmpl.id,
                        "create": False,
                    },
                }
            )
            return action
        return {"type": "ir.actions.act_window_close"}


class WizardCreateVariantLine(models.TransientModel):
    _name = "wizard.simple.create.variant.line"
    _description = "Wizard Create Variant Line"

    wizard_id = fields.Many2one(
        comodel_name="wizard.simple.create.variant",
        string="Wizard",
        required=False,
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute",
        string="Attribute",
        required=False,
    )
    attribute_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="wizard_create_variant_line_value_rel",
        column1="wizard_line_id",
        column2="value_id",
        string="Attribute Values",
    )
    selected_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="wizard_create_variant_line_selected_value_rel",
        column1="wizard_line_id",
        column2="value_id",
        string="Selected Values",
    )
    required = fields.Boolean(string="Required?", required=False)
