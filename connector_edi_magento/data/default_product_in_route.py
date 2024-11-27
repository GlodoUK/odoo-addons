# ruff: noqa
DEFAULT_PRODUCT_IN_ROUTE = """# Example Magento Product Import Code:
product = json.loads(record.body)
if not product.get("id"):
    raise UserError(_("No product id found in envelope body"))
product_id = env["edi.product.template"].search([
    ("edi_external_id", "=", product["id"])
]).odoo_id

# Do product create/update
vals = {
    "name": product.get("name", ""),
    "default_code": product.get("sku", ""),
    "weight": product.get("weight", 0),
    "list_price": product.get("price", 0),
    "detailed_type": "product",
    "type": "product",
}

# Magento Attribute Set
att_set = env["magento.attribute.set"].search([
    ("magento_id", "=", product["attribute_set_id"])
])
if not att_set:
    raise UserError("Attribute Set Not Found")
vals["magento_attribute_set_id"] = att_set.id

# Magento Attributes
magento_attributes = []
for attribute in product.get("custom_attributes", []):
    att = env["magento.attribute"].search([("code", "=", attribute["attribute_code"])])
    if not att:
        raise UserError("Attribute %s Not Found" % attribute["attribute_code"])

    if att.is_selection:
        if isinstance(attribute["value"], list):
            value_ids = env["magento.attribute.option"].search([
                ("attribute_id", "=", att.id),
                ("value", "in", attribute["value"])
            ]).ids
        else:
            value_ids = env["magento.attribute.option"].search([
                ("attribute_id", "=", att.id),
                ("value", "in", attribute["value"].split(","))
            ]).ids
        magento_attributes.append((0, 0, {
            "attribute_id": att.id, "selected_value": [(6, 0, value_ids)]
        }))
    else:
        value = attribute["value"]
        value_type = (
            "boolean" if att.frontend_input == "boolean"
            else "date" if att.frontend_input in ["datetime", "special_to_date"]
            else "int" if att.frontend_input == "int"
            else "float" if att.frontend_input == "decimal"
            else "multi_text" if att.frontend_input == "text"
            else "text"
        )
        if value_type == "boolean":
            value = True if value == "1" else False
        magento_attributes.append((0, 0, {
            "attribute_id": att.id, "%s_value" % value_type: value
        }))
if magento_attributes:
    vals["magento_attributes"] = magento_attributes

if product_id:
    # Override Attributes
    if record.envelope_route_id.magento_override_existing_products:
        vals.pop("type")
        vals.pop("detailed_type")
        vals["magento_attributes"] = [(5, 0, 0)] + vals["magento_attributes"]
        product_id.write(vals)
    else:
        record.message_post(body=_("Product %s already exists, skipped") % product["id"])
else:
    vals.update({
        "edi_external_id": product["id"],
        "backend_id": backend.id,
        "edi_message_id": record.id
    })
    product_id = env["edi.product.template"].with_context(skip_edi_push=True).create(vals)
"""
