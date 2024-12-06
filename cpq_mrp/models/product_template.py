from odoo import _, api, fields, models


class ProductAttribute(models.Model):
    _inherit = "product.attribute.value"

    cpq_allow_dynamic_bom_quantity = fields.Boolean(
        compute="_compute_cpq_allow_dynamic_bom_quantity", store=True
    )

    @api.depends("is_custom", "cpq_custom_type")
    def _compute_cpq_allow_dynamic_bom_quantity(self):
        for record in self:
            record.cpq_allow_dynamic_bom_quantity = (
                record.is_custom and record.cpq_custom_type in ("integer", "float")
            )


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    cpq_allow_dynamic_bom_quantity = fields.Boolean(
        related="product_attribute_value_id.cpq_allow_dynamic_bom_quantity",
        store=True,
        index=True,
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cpq_dynamic_bom_ids = fields.One2many("cpq.dynamic.bom", "product_tmpl_id")
    cpq_dynamic_bom_count = fields.Integer(
        compute="_compute_cpq_dynamic_bom_count", store=True
    )

    def _cpq_tooltip_items(self):
        self.ensure_one()
        res = super()._cpq_tooltip_items()
        res.extend(
            [
                _(
                    "Configurable Products can be used in conjunction with"
                    " Configurable Dynamic BoMs to generate kits and manufacturing"
                    " orders dynamically, on-demand."
                ),
            ]
        )

        if self.bom_count > 0 and self.cpq_dynamic_bom_count > 0:
            res.extend(
                [
                    "<b class='text-danger'>{}</b>".format(
                        _(
                            "You have both Standard and Configurable BoMs"
                            " configured! This will result in inconsistent BoM"
                            " handling!"
                        )
                    )
                ]
            )

        return res

    @api.depends("cpq_ok", "bom_ids", "cpq_dynamic_bom_ids")
    def _compute_cpq_tooltip(self):
        return super()._compute_cpq_tooltip()

    @api.depends("cpq_ok", "cpq_dynamic_bom_ids", "cpq_dynamic_bom_ids.active")
    def _compute_cpq_dynamic_bom_count(self):
        for record in self:
            if not record.cpq_ok:
                record.cpq_dynamic_bom_count = 0
                continue
            record.cpq_dynamic_bom_count = len(record.cpq_dynamic_bom_ids)

    def action_view_cpq_dynamic_bom(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Configurable Products Bill of Materials"),
            "res_model": "cpq.dynamic.bom",
            "view_mode": "form",
            "res_id": self.cpq_dynamic_bom_ids.id,
        }

    def write(self, vals):
        if not self.env.context.get("cpq_mrp_skip_auto_archive", False):
            if vals.get("cpq_ok") is False:
                for record in self.sudo().filtered(
                    lambda p: p.cpq_ok and p.cpq_dynamic_bom_ids
                ):
                    record.cpq_dynamic_bom_ids.message_post(
                        body=_(
                            "Archived due product template not longer being \
                                configurable"
                        )
                    )
                    record.cpq_dynamic_bom_ids.write({"active": False})

            if vals.get("active") is False:
                for record in self.sudo().filtered(
                    lambda p: p.active and p.cpq_dynamic_bom_ids
                ):
                    record.cpq_dynamic_bom_ids.message_post(
                        body=_("Archived due to product template being archived")
                    )
                    record.cpq_dynamic_bom_ids.write({"active": False})

        return super().write(vals)
