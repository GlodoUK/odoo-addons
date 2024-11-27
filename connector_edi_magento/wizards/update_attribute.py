from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardMagentoUpdateAttribute(models.TransientModel):
    _name = "wizard.magento.update.attribute"
    _description = "Update Magento Attribute Wizard"

    backend_id = fields.Many2one("edi.backend", string="Magento Backend", required=True)
    attribute_id = fields.Many2one("magento.attribute", string="Attribute")
    product_ids = fields.Many2many("product.template", string="Products")
    value = fields.Char(compute="_compute_value")

    available_attribute_ids = fields.Many2many("magento.attribute")

    selected_value = fields.Many2many(
        "magento.attribute.option",
        domain="[('attribute_id', '=', attribute_id)]",
    )
    field_type = fields.Selection(related="attribute_id.field_type")
    frontend_input = fields.Selection(related="attribute_id.frontend_input")
    text_value = fields.Char()
    multi_text_value = fields.Char()
    date_value = fields.Datetime()
    boolean_value = fields.Boolean()
    float_value = fields.Float()
    int_value = fields.Integer()

    is_selection = fields.Boolean(related="attribute_id.is_selection")
    is_single_select = fields.Boolean(related="attribute_id.is_single_select")
    readonly = fields.Boolean(related="attribute_id.readonly")

    def default_get(self, fields):
        res = super().default_get(fields)

        active_ids = self.env.context.get("active_ids")
        if not active_ids:
            raise UserError(_("No product selected!"))

        product_ids = self.env["product.template"].sudo().browse(active_ids)
        if not product_ids:
            raise UserError(_("No products found!"))

        backend_id = product_ids.mapped("magento_attributes.attribute_id.backend_id")
        if len(backend_id) > 1:
            raise UserError(_("Cannot update products from multiple backends!"))

        attributes = product_ids.mapped("magento_attributes.attribute_id")
        for product in product_ids:
            attributes = attributes & product.magento_attributes.mapped("attribute_id")
        if not attributes:
            raise UserError(
                _(
                    "No common attributes found!"
                    " Please ensure all selected products have the same available"
                    " attributes"
                )
            )
        available_attribute_ids = attributes

        res.update(
            {
                "product_ids": [(6, 0, product_ids.ids)],
                "backend_id": backend_id.id,
                "available_attribute_ids": [(6, 0, available_attribute_ids.ids)],
            }
        )

        return res

    def update_attributes(self):
        self.ensure_one()
        for product in self.sudo().product_ids:
            attribute_record = product.magento_attributes.filtered(
                lambda x: x.attribute_id == self.attribute_id
            )
            field_type = self.attribute_id.frontend_input
            if self.attribute_id.is_selection:
                field_type = "selected"
            if self.attribute_id.frontent_input == "textarea":
                field_type = "multi_text"
            if self.attribute_id.frontend_input in ["price", "weight"]:
                field_type = "float"
            field_value = getattr(self, "%s_value" % field_type)
            attribute_record.write(
                {
                    "%s_value" % field_type: field_value,
                }
            )
        return {"type": "ir.actions.act_window_close"}

    @api.onchange(
        "attribute_id",
        "selected_value",
        "text_value",
        "date_value",
        "boolean_value",
        "int_value",
        "float_value",
        "multi_text_value",
    )
    def _compute_value(self):
        for record in self:
            if record.is_selection:
                if record.is_single_select:
                    record.value = fields.first(record.selected_value).name
                else:
                    record.value = ",".join(record.selected_value.mapped("name"))
            elif record.frontend_input == "boolean":
                record.value = "True" if record.boolean_value else "False"
            elif record.frontend_input in ["datetime", "special_to_date"]:
                record.value = record.date_value
            elif record.frontend_input == "int":
                record.value = str(record.int_value)
            elif record.frontend_input == "decimal":
                record.value = str(record.float_value)
            elif record.frontend_input == "text":
                record.value = record.multi_text_value
            else:
                record.value = record.text_value
