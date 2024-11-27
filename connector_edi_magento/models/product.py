from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    magento_attribute_set_id = fields.Many2one(
        "magento.attribute.set",
        string="Magento Attribute Set",
        help="Magento Attribute Set",
    )
    magento_attributes = fields.One2many("magento.attribute.selection", "product_id")
    image_1920 = fields.Binary(readonly=True)

    def write(self, values):
        res = super().write(values)
        if "magento_attributes" in values:
            for record in self:
                ids = []
                for magento_attribute in record.magento_attributes:
                    if magento_attribute.attribute_id.id in ids:
                        raise ValidationError(
                            _("Duplicate Magento Attribute '%s' Found!")
                            % magento_attribute.attribute_id.name
                        )
                    ids.append(magento_attribute.attribute_id.id)
        attributes = self.env["magento.attribute"].search([])
        for value in values:
            if value in attributes.mapped_field.mapped("name"):
                for record in self:
                    att = self.magento_attributes.filtered(
                        lambda a, value=value: a.mapped_field.name == value
                    )
                    if not att:
                        attribute = attributes.filtered(
                            lambda a, value=value: a.mapped_field.name == value
                        )
                        att = self.magento_attributes.create(
                            {
                                "product_id": record.id,
                                "attribute_id": attribute.id,
                            }
                        )
                    att.with_context(prevent_loop=True).update_value(values.get(value))
        return res

    def _get_magento_attributes(self, export_format=False):
        self.ensure_one()
        return [
            {
                "attribute_code": attribute.attribute_id.code,
                "value": attribute._get_magento_value(export_format),
            }
            for attribute in self.magento_attributes.filtered(
                lambda a: not a.attribute_id.readonly
            )
            if attribute._get_magento_value(export_format)
        ]

    def _get_magento_stock_attributes(self):
        self.ensure_one()
        in_stock = True if self.qty_available > 0 else False

        return [
            {
                "attribute_code": "stock_status",
                "value": 1 if in_stock else 0,
            }
        ]

    def _get_monitor_fields(self):
        fields = super()._get_monitor_fields()
        fields.append("magento_attributes")
        return fields

    def action_push_to_magento(self):
        self.ensure_one()
        self = self.sudo()

        if not self.edi_product_tmpl_ids:
            backend_ids = self.env["edi.backend"].search([("is_magento", "=", True)])
            to_bind = []

            for backend_id in backend_ids:
                to_bind.append(
                    (
                        0,
                        0,
                        {
                            "backend_id": backend_id.id,
                            "odoo_id": self.id,
                        },
                    )
                )

            if to_bind:
                self.write(
                    {
                        "edi_product_tmpl_ids": to_bind,
                    }
                )

        for binding_id in self.edi_product_tmpl_ids:
            # TODO: Remove this and trigger an event instead, that way we are
            # not double triggering
            self.env["edi.route"].sudo().send_messages_using_first_match(
                binding_id.backend_id,
                self,
                [
                    ("envelope_route_id.magento_endpoint", "=", "products/"),
                    ("direction", "=", "out"),
                    ("model_event_id.res_model", "=", self._name),
                    ("action_trigger", "=", "model_event"),
                ],
            )

    @api.model
    def handle_magento_response(self, response, backend_id):
        product_data = response.json()
        product_id = product_data.get("id")
        sku = product_data.get("sku")
        product_template = self.env["product.template"].search(
            [("default_code", "=", sku)]
        )
        if product_template:
            edi_product = product_template.edi_product_tmpl_ids.filtered(
                lambda r: r.backend_id == backend_id
            )
            if edi_product:
                edi_product.write({"edi_external_id": product_id})
            else:
                self.env["edi.product.template"].create(
                    {
                        "backend_id": backend_id.id,
                        "odoo_id": product_template.id,
                        "edi_external_id": product_id,
                    }
                )
        return product_template


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_monitor_fields(self):
        fields = super()._get_monitor_fields()
        fields.append("magento_attributes")
        return fields

    def _get_magento_attributes(self, export_format=False):
        self.ensure_one()
        return [
            {
                "attribute_code": attribute.attribute_id.code,
                "value": attribute._get_magento_value(export_format),
            }
            for attribute in self.magento_attributes.filtered(
                lambda a: not a.attribute_id.readonly
            )
        ]

    def _get_magento_stock_attributes(self):
        self.ensure_one()
        return self.product_tmpl_id._get_magento_stock_attributes()

    def action_push_to_magento(self):
        self.ensure_one()
        self.product_tmpl_id.action_push_to_magento()
