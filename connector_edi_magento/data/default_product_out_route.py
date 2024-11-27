# ruff: noqa
DEFAULT_PRODUCT_OUT_ROUTE = """# Example Magento Product Export Code:
product = record

sku = product.default_code
if not sku:
    raise UserError(
        _("No product sku found for product ID {product_id}").format(
            product_id=product.id)
    )
product_data = {
    "product": {
        'sku': sku,
        'name': product.name,
        # ID 4 is 'Default'
        'attribute_set_id': product.magento_attribute_set_id.magento_id or 4,
        'price': product.list_price,
        'status': 1 if product.active else 0,
        'weight': product.weight,
    }
}

edi_record = product.edi_product_tmpl_ids.filtered(
    lambda r: r.backend_id == backend
)

stock_qty = product.qty_available
if edi_record:
  item_id = 0
  product_data["product"]["id"] = edi_record.edi_external_id
  # Stock Item
  response = backend.magento_send_request(
  "stockItems/{sku}".format(sku=sku), method="GET"
  )
  if response.status_code == 200:
    stock_items = json.loads(response.content)
    item_id = stock_items.get("item_id", 0)
    product_data["product"]["extension_attributes"] = {
        "stock_item": {
          "item_id" : item_id,
          "is_in_stock" : stock > 0,
          "qty" : stock_qty
        }
      }
else:
  product_data["product"]["extension_attributes"] = {
      "stock_item" : {
        "qty": stock_qty
      }
    }


product_data["product"]["custom_attributes"] = product._get_magento_attributes(True)
product_data["product"]["custom_attributes"] += product._get_magento_stock_attributes()


external_id = 'MagentoOut-Product-%s_%s' % (
    product.default_code, product.write_date.strftime('%Y%m%dT%H%M%S')
)
msg = env["edi.message"].create({
    'direction': 'out',
    'backend_id': backend.id,
    'body': json.dumps(product_data),
    'message_route_id': route_id.id,
    'external_id': external_id,
    'content_filename': external_id + '.json',
})
msg.action_pending()

"""
