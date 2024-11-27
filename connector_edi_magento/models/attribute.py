import logging
import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

FIELD_TYPE_MAP = {
    "boolean": "boolean",
    "int": "integer",
    "price": "float",
    "weight": "float",
    "text": "char",
    "textarea": "text",
    "select": "many2one",
    "multiselect": "many2many",
    "date": "datetime",
    "media_image": "binary",
    "media_gallery": "binary",
}


class MagentoAttributeSet(models.Model):
    _name = "magento.attribute.set"
    _description = "Magento Attribute Set"

    name = fields.Char(required=True)
    magento_id = fields.Integer(required=True)
    attribute_ids = fields.Many2many(
        "magento.attribute",
        relation="magento_attribute_set_attribute_rel",
        column1="attribute_set_id",
        column2="attribute_id",
        string="Attributes",
    )
    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        string="Magento Backend",
        required=True,
        ondelete="cascade",
    )


class MagentoAttribute(models.Model):
    _name = "magento.attribute"
    _description = "Magento Attribute"
    _order = "readonly ASC, sequence ASC, magento_id ASC"

    magento_id = fields.Integer(string="Magento ID", required=True)
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    field_type = fields.Selection(
        [
            ("static", "Char"),
            ("varchar", "VarChar"),
            ("text", "Text"),
            ("decimal", "Float"),
            ("datetime", "Datetime"),
            ("special_to_date", "Special To Date"),
            ("int", "Integer"),
            ("multiselect", "Many2many"),
            ("boolean", "Boolean"),
            ("intlist", "Integer List"),
        ],
    )
    frontend_input = fields.Selection(
        [
            ("text", "Text"),
            ("textarea", "Textarea"),
            ("date", "Date"),
            ("boolean", "Boolean"),
            ("multiselect", "Many2many"),
            ("select", "Selection"),
            ("price", "Price"),
            ("weight", "Weight"),
            ("media_image", "Media Image"),
            ("gallery", "Gallery"),
        ],
    )
    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        string="Magento Backend",
        required=True,
        ondelete="cascade",
    )
    options = fields.Many2many("magento.attribute.option")
    is_selection = fields.Boolean(compute="_compute_is_selection")
    is_single_select = fields.Boolean()

    mapped_field = fields.Many2one(
        "ir.model.fields",
        domain="[('model_id.model', '=', 'product.template')]",
        help="When this attribute is updated"
        ", the value will be copied to this field, and vice versa",
    )

    readonly = fields.Boolean()
    sequence = fields.Integer(
        string="Weighting", help="Lower Weighting = higher priority"
    )

    def _compute_is_selection(self):
        for record in self:
            record.is_selection = record.frontend_input in [
                "select",
                "multiselect",
            ] or (len(record.options) > 0 and record.frontend_input != "boolean")

    def write(self, vals):
        if "mapped_field" in vals and vals["mapped_field"]:
            field = self.env["ir.model.fields"].sudo().browse(vals["mapped_field"])
            if field.ttype != FIELD_TYPE_MAP[self.frontend_input]:
                raise ValidationError(
                    _("The field type of the mapped field must be {field_type}").format(
                        field_type=FIELD_TYPE_MAP[self.frontend_input]
                    )
                )
        return super().write(vals)

    @api.model
    def fetch_magento_attributes(
        self, backend, ignore_attributes=None, readonly_attributes=None, page_size=500
    ):
        """
        Sync attributes from Magento
        """
        # TODO: Make this a sync instead of a pull
        _logger.info("Fetch Magento Attributes for backend %s", backend.name)

        # Attributes
        current_page = 1
        params = {
            "searchCriteria[currentPage]": current_page,
            "searchCriteria[pageSize]": page_size,
        }
        response = backend.magento_send_request("products/attributes/", params=params)
        if response.status_code != 200:
            raise UserError(_("Error fetching attributes from Magento"))
        total_count = response.json()["total_count"]
        total_pages = math.ceil(total_count / page_size)

        while current_page <= total_pages:
            if current_page == 1:
                attributes = response.json().get("items", [])
                self._process_attributes(
                    attributes, backend, ignore_attributes, readonly_attributes
                )
            else:
                params["searchCriteria[currentPage]"] = current_page
                response = backend.magento_send_request(
                    "products/attributes/", params=params
                )
                if response.status_code != 200:
                    raise UserError(
                        _(
                            "Error fetching attributes page {current_page} from Magento"
                        ).format(current_page=current_page)
                    )
                attributes = response.json().get("items", [])
                self._process_attributes(
                    attributes, backend, ignore_attributes, readonly_attributes
                )
            current_page += 1

        # Attribute Sets
        current_page = 1
        params = {
            "searchCriteria[currentPage]": current_page,
            "searchCriteria[pageSize]": page_size,
        }
        response = backend.magento_send_request(
            "products/attribute-sets/sets/list", params=params
        )
        if response.status_code != 200:
            raise UserError(_("Error fetching attribute sets from Magento"))
        total_count = response.json()["total_count"]
        total_pages = math.ceil(total_count / page_size)

        while current_page <= total_pages:
            if current_page == 1:
                attributes = response.json().get("items", [])
                self._process_attribute_sets(attributes, backend)
            else:
                params["searchCriteria[currentPage]"] = current_page
                response = backend.magento_send_request(
                    "products/attribute-sets/sets/list", params=params
                )
                if response.status_code != 200:
                    raise UserError(
                        _(
                            "Error fetching attribute sets page {current_page} from"
                            " Magento"
                        ).format(current_page=current_page)
                    )
                attributes = response.json().get("items", [])
                self._process_attribute_sets(attributes, backend)
            current_page += 1

        # Product Categories
        _logger.info("Fetch Magento Product Categories for backend %s", backend.name)

        # Attributes
        current_page = 1
        params = {
            "searchCriteria[currentPage]": current_page,
            "searchCriteria[pageSize]": page_size,
        }
        response = backend.magento_send_request("categories/list/", params=params)
        if response.status_code != 200:
            raise UserError(_("Error fetching categories from Magento"))
        total_count = response.json()["total_count"]
        total_pages = math.ceil(total_count / page_size)

        while current_page <= total_pages:
            if current_page == 1:
                categories = response.json().get("items", [])
                self._process_categories(categories, backend)
            else:
                params["searchCriteria[currentPage]"] = current_page
                response = backend.magento_send_request(
                    "categories/list/", params=params
                )
                if response.status_code != 200:
                    raise UserError(
                        _(
                            "Error fetching categories page {current_page} from Magento"
                        ).format(current_page=current_page)
                    )
                categories = response.json().get("items", [])
                self._process_categories(categories, backend)
            current_page += 1

    def _process_attributes(
        self, attributes, backend, ignore_attributes=None, readonly_attributes=None
    ):
        for attribute in attributes:
            if attribute["attribute_code"] in (ignore_attributes or []):
                continue
            att = self.env["magento.attribute"].search(
                [
                    ("backend_id", "=", backend.id),
                    ("magento_id", "=", attribute["attribute_id"]),
                ]
            )
            if not att:
                att = self.env["magento.attribute"].search(
                    [
                        ("backend_id", "=", backend.id),
                        ("code", "=", attribute["attribute_code"]),
                    ]
                )
                # Force the attribute ID in case it's missing (for migrations)
                if att:
                    att.magento_id = attribute["attribute_id"]
            # Only create new attributes. Do not overwrite existing attributes
            if not att:
                readonly = False
                if attribute["attribute_code"] in (readonly_attributes or []):
                    readonly = True
                # Special case for Categories
                if attribute["attribute_code"] == "category_ids":
                    attribute["frontend_input"] = "multiselect"
                    attribute["backend_type"] = "intlist"
                att = self.env["magento.attribute"].create(
                    {
                        "backend_id": backend.id,
                        "magento_id": attribute["attribute_id"],
                        "code": attribute["attribute_code"],
                        "name": attribute.get(
                            "default_frontend_label", attribute["attribute_code"]
                        ),
                        "field_type": attribute["backend_type"],
                        "frontend_input": attribute["frontend_input"],
                        "is_single_select": attribute["frontend_input"] == "select",
                        "readonly": readonly,
                    }
                )

            # Add any new options to the attribute
            options = []
            if attribute["frontend_input"] != "boolean":
                for option in attribute.get("options", []):
                    if (
                        option["label"]
                        and option["label"] not in ["", " "]
                        and option["label"] not in att.options.mapped("name")
                    ):
                        options.append(
                            (
                                0,
                                0,
                                {
                                    "attribute_id": att.id,
                                    "name": option["label"],
                                    "value": option["value"],
                                },
                            )
                        )
            att.options = options

    def _process_attribute_sets(self, attributes, backend):
        for attribute in attributes:
            att_set = self.env["magento.attribute.set"].search(
                [
                    ("backend_id", "=", backend.id),
                    ("magento_id", "=", attribute["attribute_set_id"]),
                ]
            )
            # Only create new attribute sets. Do not overwrite existing attribute sets
            if not att_set:
                response = backend.magento_send_request(
                    "products/attribute-sets/{set_id}/attributes".format(
                        set_id=attribute["attribute_set_id"]
                    )
                )
                if response.status_code != 200:
                    raise UserError(
                        _(
                            "Error fetching attributes for attribute set {set_id} from"
                            " Magento"
                        ).format(set_id=attribute["attribute_set_id"])
                    )
                att_json = response.json()
                att_list = []
                for att in att_json:
                    att = self.env["magento.attribute"].search(
                        [
                            ("backend_id", "=", backend.id),
                            ("magento_id", "=", att["attribute_id"]),
                        ]
                    )
                    if att:
                        att_list.append((4, att.id))
                self.env["magento.attribute.set"].create(
                    {
                        "backend_id": backend.id,
                        "magento_id": attribute["attribute_set_id"],
                        "name": attribute["attribute_set_name"],
                        "attribute_ids": att_list,
                    }
                )

    def _process_categories(self, categories, backend):
        category_attribute = self.env["magento.attribute"].search(
            [("backend_id", "=", backend.id), ("code", "=", "category_ids")]
        )
        dummy_attribute = {
            "attribute_code": "category_ids",
            "frontend_input": "multiselect",
            "backend_type": "intlist",
            "attribute_id": category_attribute.magento_id,
            "options": [],
        }
        for category in categories:
            dummy_attribute["options"].append(
                {
                    "label": category["name"],
                    "value": category["id"],
                }
            )
        self._process_attributes([dummy_attribute], backend)


class MagentoAttributeOption(models.Model):
    _name = "magento.attribute.option"
    _description = "Magento Attribute Option"

    attribute_id = fields.Many2one(
        "magento.attribute",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(
        required=True,
    )
    value = fields.Char(
        required=True,
    )


class MagentoAttributeSelection(models.Model):
    _name = "magento.attribute.selection"
    _description = "Magento Attribute Selection"
    _order = "readonly ASC, sequence ASC"

    attribute_set_id = fields.Many2one(
        "magento.attribute.set",
    )
    attribute_id = fields.Many2one(
        "magento.attribute",
        ondelete="cascade",
    )
    available_attribute_ids = fields.Many2many(related="attribute_set_id.attribute_ids")
    product_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
    )
    selected_value = fields.Many2many(
        "magento.attribute.option",
        domain="[('attribute_id', '=', attribute_id)]",
    )
    field_type = fields.Selection(related="attribute_id.field_type")
    frontend_input = fields.Selection(related="attribute_id.frontend_input")
    text_value = fields.Char(inverse="_inverse_update_mapped_field")
    multi_text_value = fields.Text(inverse="_inverse_update_mapped_field")
    date_value = fields.Datetime(inverse="_inverse_update_mapped_field")
    boolean_value = fields.Boolean(inverse="_inverse_update_mapped_field")
    float_value = fields.Float(inverse="_inverse_update_mapped_field")
    int_value = fields.Integer(inverse="_inverse_update_mapped_field")
    final_value = fields.Char(compute="_compute_final_value")

    is_selection = fields.Boolean(related="attribute_id.is_selection")
    is_single_select = fields.Boolean(related="attribute_id.is_single_select")
    readonly = fields.Boolean(compute="_compute_sequence_readonly", store=True)
    sequence = fields.Integer(compute="_compute_sequence_readonly", store=True)

    mapped_field = fields.Many2one(related="attribute_id.mapped_field")

    @api.depends("attribute_id.sequence", "attribute_id.readonly")
    def _compute_sequence_readonly(self):
        for record in self:
            record.sequence = record.attribute_id.sequence
            record.readonly = record.attribute_id.readonly

    @api.onchange(
        "attribute_id",
        "selected_value",
        "text_value",
        "multi_text_value",
        "date_value",
        "boolean_value",
        "int_value",
        "float_value",
    )
    def _compute_final_value(self):
        for record in self:
            if record.is_selection:
                if record.is_single_select:
                    record.final_value = fields.first(record.selected_value).name
                else:
                    record.final_value = ", ".join(record.selected_value.mapped("name"))
            elif record.frontend_input == "boolean":
                record.final_value = "True" if record.boolean_value else "False"
            elif record.frontend_input == "date":
                record.final_value = (
                    record.date_value.isoformat() if record.date_value else ""
                )
            elif record.frontend_input == "int":
                record.final_value = str(record.int_value)
            elif record.frontend_input in ["price", "weight"]:
                record.final_value = str(record.float_value)
            elif record.frontend_input == "textarea":
                record.final_value = record.multi_text_value
            else:
                record.final_value = record.text_value

    @api.onchange("selected_value")
    def _onchange_selected_value(self):
        if self.is_single_select:
            if len(self.selected_value) > 1:
                raise ValidationError(
                    _("You can only select one value for this attribute.")
                )

    def _get_magento_value(self, export_format=False):
        self.ensure_one()
        if self.is_selection:
            if export_format:
                return self._format_selection()
            if self.is_single_select:
                return fields.first(self.selected_value).name or ""
            else:
                return ", ".join(self.selected_value.mapped("name"))
        elif self.frontend_input == "boolean":
            if export_format:
                return "1" if self.boolean_value else "0"
            return True if self.boolean_value else False
        elif self.frontend_input in ["date"]:
            if not self.date_value:
                return ""
            return self.date_value.strftime("%d-%m-%Y")
        elif self.frontend_input == "int":
            if export_format:
                return self.int_value or 0
            return str(self.int_value or 0)
        elif self.frontend_input in ["price", "weight"]:
            if export_format:
                return self.float_value or 0.0
            return str(self.float_value or 0.0)
        elif self.frontend_input == "textarea":
            return self.multi_text_value or ""
        else:
            return self.text_value or ""

    def _format_selection(self):
        self.ensure_one()
        if self.is_single_select:
            if self.field_type == "int":
                return int(self.selected_value.value)
            else:
                return self.selected_value.value
        elif self.field_type == "intlist":
            return [int(value.value) for value in self.selected_value]
        else:
            return str(self.selected_value.mapped("value"))

    def update_value(self, value):
        if self.frontend_input == "boolean":
            self.boolean_value = value
        elif self.frontend_input == "date":
            self.date_value = value
        elif self.frontend_input == "int":
            self.int_value = int(value)
        elif self.frontend_input in ["price", "weight"]:
            self.float_value = float(value)
        elif self.frontend_input == "multiselect":
            self.selected_value = [(6, 0, value.ids)]
        elif self.frontend_input == "select":
            self.selected_value = [(6, 0, [value.id])]
        elif self.frontend_input == "textarea":
            self.multi_text_value = value
        else:
            self.text_value = value

    def _inverse_update_mapped_field(self):
        if self._context.get("prevent_loop", False):
            return
        for record in self:
            if record.mapped_field:
                if record.frontend_input == "boolean":
                    record.product_id[record.mapped_field.name] = record.boolean_value
                elif record.frontend_input == "date":
                    record.product_id[record.mapped_field.name] = record.date_value
                elif record.frontend_input == "int":
                    record.product_id[record.mapped_field.name] = record.int_value
                elif record.frontend_input in ["price", "weight"]:
                    record.product_id[record.mapped_field.name] = record.float_value
                elif record.frontend_input == "multiselect":
                    record.product_id[
                        record.mapped_field.name
                    ] = record.selected_value.ids
                elif record.frontend_input == "select":
                    record.product_id[
                        record.mapped_field.name
                    ] = record.selected_value.id
                elif record.frontend_input == "textarea":
                    record.product_id[
                        record.mapped_field.name
                    ] = record.multi_text_value
                else:
                    record.product_id[record.mapped_field.name] = record.text_value
