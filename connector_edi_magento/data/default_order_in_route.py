# ruff: noqa

DEFAULT_ORDER_IN_ROUTE = """# Example Magento Order Import Code:
order = json.loads(record.body)
order_id = (
  env["edi.sale.order"]
  # for backwards compat with OCA/connector_magento
  .search([
    ('backend_id', '=', backend.id),
    ("edi_external_id", "=", str(order["entity_id"]))
  ])
  .odoo_id
)

envelope_route_id = record.envelope_route_id

paid = order.get("base_total_paid")
payment_method = order.get("payment", {}).get("method")
order_status = order.get("status")

if order_id:
    # Update existing order
    # TODO: Handle address updates and changes

    if order_status in ["canceled", "cancelled"]:
        # Cancel order
        if order_id.state != "cancel":
            order_id.action_cancel()
    elif not paid:
        # Order still not yet paid, ignore update.
        pass
    elif order_id.invoice_status == "invoiced":
        # Order already invoiced
        invoices = order_id.invoice_ids
        if "not_paid" not in invoices.mapped("state"):
            # All invoices paid or in payment
            record.message_post(body="Order already invoiced and paid")
        else:
            if paid:
                # Order considered paid
                journal_id = env.ref("connector_edi_magento.edi_magento_journal")
                payment_name = move_id.name
                if order.get("payment", False):
                    if payment_method:
                        payment_id = order["payment"].get("cc_trans_id", False)
                        if payment_id:
                            payment_name = "%s (%s) - %s" % (
                                payment_id,
                                payment_method,
                                payment_name,
                            )
                        else:
                            payment_name = "%s - %s" % (payment_method, payment_name)
                env["account.payment.register"].with_context(
                    active_model="account.move",
                    active_ids=move_id.id,
                    default_payment_difference_handling="reconcile",
                    default_writeoff_label="Magento Rounding Difference",
                    default_writeoff_account_id=journal_id.loss_account_id.id,
                ).create(
                    {
                        "payment_date": order.get("updated_at"),
                        "journal_id": journal_id.id,
                        "amount": order.get("total_paid", 0),
                        "currency_id": move_id.currency_id.id,
                        "communication": payment_name,
                        "payment_type": "inbound",
                        "partner_type": "customer",
                        "partner_id": move_id.partner_id.id,
                    }
                )._create_payments()
                if order_id.hold:
                    order_id.action_unhold(msg="Payment Received")
            else:
                order_id.odoo_id.action_hold(msg="Payment Pending")
            record.message_post(body="Order already invoiced")
    else:
        # Raise new invoice, mark paid if applicable
        if paid:
            # Order considered invoiced
            if order_id.state in ["draft", "sent"]:
                # Order was not previously confirmed, confirm now
                order_id.action_confirm()
            move_id = order_id.odoo_id._create_invoices()
            if move_id:
                move_id.action_post()
                journal_id = env.ref("connector_edi_magento.edi_magento_journal")
                payment_name = move_id.name
                if order.get("payment", False):
                    method = order["payment"].get("method", False)
                    if method:
                        payment_id = order["payment"].get("cc_trans_id", False)
                        if payment_id:
                            payment_name = "%s (%s) - %s" % (
                                payment_id,
                                method,
                                payment_name,
                            )
                        else:
                            payment_name = "%s - %s" % (method, payment_name)
                env["account.payment.register"].with_context(
                    active_model="account.move",
                    active_ids=move_id.id,
                    default_payment_difference_handling="reconcile",
                    default_writeoff_label="Magento Rounding Difference",
                    default_writeoff_account_id=journal_id.loss_account_id.id,
                ).create(
                    {
                        "payment_date": order.get("updated_at"),
                        "journal_id": journal_id.id,
                        "amount": paid,
                        "currency_id": move_id.currency_id.id,
                        "communication": payment_name,
                        "payment_type": "inbound",
                        "partner_type": "customer",
                        "partner_id": move_id.partner_id.id,
                    }
                )._create_payments()
                if order_id.hold:
                    order_id.action_unhold(msg="Payment Received")
            record.message_post(body="Order invoice status updated")

elif (
    order_status in ["canceled", "cancelled"]
    and envelope_route_id.magento_skip_cancelled_orders
):
    # Skip Cancelled orders if configured
    record.message_post(body="Magento Order cancelled, skipping")
elif (
    not paid and order.get("base_total_due", 0) != 0
    and envelope_route_id.magento_skip_unpaid_orders
):
    # Skip Upaid orders if configured
    record.message_post(body="Magento Order unpaid, skipping")
else:
    # Create new order

    # Customer Address (Main Partner)
    customer_is_guest = bool(order.get("customer_is_guest", False))
    customer_id = order.get("customer_id", False)
    billing = order.get("billing_address")
    billing_id = order.get("billing_address_id", False)
    customer_email = order.get("customer_email", billing.get("email", "")) or ""

    company_name = billing.get("company", False)
    customer_name = (
        (
            (order.get("customer_firstname", billing.get("firstname")) or "")
            + " "
            + (order.get("customer_lastname", billing.get("lastname")) or "")
        )
        .strip()
        .title()
    )

    partner_id = env["edi.res.partner"]

    if customer_id:
        customer_id_domain = [
            ('backend_id', '=', backend.id),
        ]
        if customer_is_guest:
            customer_id_domain.extend([
                ("magento_customer_is_guest", "=", True),
                ("email", "=", customer_email)
            ])
        else:
            customer_id_domain.extend([
                ('magento_customer_is_guest', '=', False),
                ("edi_external_id", "=", str(customer_id))
            ])

        partner_id = env["edi.res.partner"].search(customer_id_domain, limit=1)

    partner_vals = {
        "name": customer_name,
        "email": customer_email,
        "street": billing["street"][0],
        "city": billing["city"],
        "zip": billing["postcode"],
        "country_id": env["res.country"].search([("code", "=", billing["country_id"])]).id,
        "phone": billing["telephone"],
        "company_type": "person" if company_name else "company",
        "magento_customer_is_guest": customer_is_guest,
    }
    if len(billing["street"]) > 1:
        partner_vals["street2"] = billing["street"][1]

    if not partner_id:
        partner_vals.update({
            "backend_id": backend.id,
            "edi_external_id": str(customer_id),
            "magento_customer_is_guest": customer_is_guest,
        })

        partner_id = env["edi.res.partner"].create(partner_vals)
    else:
        # Update partner for latest vals
        partner_id.write(partner_vals)

    # Billing Address
    billing_contact = env['edi.magento.address']
    if billing_id:
        billing_contact = env["edi.magento.address"].search([
            ("edi_external_id", "=", str(billing_id)),
            ('backend_id', '=', backend.id),
        ], limit=1)

        billing = order["billing_address"]
        billing_name = (
            (
                (billing.get("firstname", "") or "")
                + " "
                + (billing.get("lastname", "") or "")
            )
            .strip()
            .title()
        )
        billing_vals = {
            "name": billing_name,
            "email": billing.get("email", "") or "",
            "street": billing["street"][0],
            "city": billing["city"],
            "zip": billing["postcode"],
            "country_id": env["res.country"].search([("code", "=", billing["country_id"])]).id,
            "phone": billing["telephone"],
        }
        if len(billing["street"]) > 1:
            billing_vals["street2"] = billing["street"][1]

        if billing_contact:
            # ensure we have the most recent info
            billing_contact.write(billing_vals)
        else:
            billing_vals.update({
                'backend_id': backend.id,
                'edi_external_id': str(billing_id),
                'parent_id': partner_id.odoo_id.id,
                'type': 'invoice',
            })
            billing_contact = env['edi.magento.address'].create(
                billing_vals
            )

    # Shipping Address (Delivery Address)
    # default to current customer
    shipping_id = env['edi.magento.address']

    shipping = (
        order.get("extension_attributes", {})
        .get("shipping_assignments", [{}])[0]
        .get("shipping", {})
    )
    if shipping:
        shipping_address = shipping.get("address", {})
        shipping_name = (
            (
                (shipping.get("firstname", shipping_address["firstname"]) or "")
                + " "
                + (shipping.get("lastname", shipping_address["lastname"]) or "")
            )
            .strip()
            .title()
        )
        shipping_vals = {
            "name": shipping_name,
            "email": shipping_address.get("email", "") or "",
            "street": shipping_address["street"][0],
            "city": shipping_address["city"],
            "zip": shipping_address["postcode"],
            "country_id": (
                env["res.country"].search([
                    ("code", "=", shipping_address["country_id"])
                ]).id
            ),
            "phone": shipping_address["telephone"],
        }
        if len(shipping_address["street"]) > 1:
            shipping_vals["street2"] = shipping_address["street"][1]

        shipping_id = env['edi.magento.address'].search([
            ('backend_id', '=', backend.id),
            ('edi_external_id', '=', str(shipping.get("entity_id"))),
        ], limit=1)

        if not shipping_id:
            shipping_vals.update({
                'backend_id': backend.id,
                "edi_external_id": str(shipping.get("entity_id")),
                'parent_id': partner_id.odoo_id.id,
                'type': 'delivery',
            })
            shipping_id = env['edi.magento.address'].create(shipping_vals)
        else:
            # update
            shipping_id.write(shipping_vals)

    # Now we can do the order
    order_date = datetime.datetime.strptime(order["created_at"], "%Y-%m-%d %H:%M:%S")

    values = {
        "backend_id": backend.id,
        "edi_message_id": record.id,
        "edi_external_id": str(order["entity_id"]),
        "date_order": order_date,
        "partner_id": partner_id.odoo_id.id,
        "partner_invoice_id": billing_contact.odoo_id.id or partner_id.odoo_id.id,
        "partner_shipping_id": shipping_id.odoo_id.id or partner_id.odoo_id.id,
        "origin": order["increment_id"],
        # propagate the original order name from Magento
        # rather than use Odoo's own name
        "name": order["increment_id"]
    }
    currency_code = order.get("base_currency_code")
    if currency_code:
        currency_id = env.ref("base.%s" % currency_code)
        if not currency_id or not currency_id.active:
            raise EdiException("Currency %s not found" % currency_code)
    else:
        currency_id = env.company.currency_id
    values["currency_id"] = currency_id.id

    # Create Empty Order
    order_id = env["edi.sale.order"].create(values)

    for line in order["items"]:
        magento_product_id = line.get("product_id")
        product_template = (
            env["edi.product.template"]
            .search([
                ("edi_external_id", "=", magento_product_id),
                ("backend_id", "=", backend.id),
            ], limit=1)
            .odoo_id
        )
        if not product_template:
            raise EdiException("Product %s not found" % magento_product_id)

        price = line.get("base_price", 0)

        tax_id = env["account.tax"]
        if line.get("tax_percent", 0) != 0:
            tax_id = env["account.tax"].search(
                [
                    ("amount", ">", line["tax_percent"] - 1),
                    ("amount", "<", line["tax_percent"] + 1),
                    ("type_tax_use", "=", "sale"),
                ],
                limit=1,
            )
            if not tax_id:
                raise EdiException("Tax %s not found" % line["tax_percent"])
        line_description = line.get("name", line.get("name", product_template.name))

        # Assume single variant templates
        product = product_template.product_variant_ids[0]
        order_line = env["sale.order.line"].create(
            {
                "order_id": order_id.odoo_id.id,
                "product_id": product.id,
                "product_uom_qty": line["qty_ordered"],
                "price_unit": price,
                "tax_id": [(6, 0, tax_id.ids)],
                "name": line_description,
            }
        )

    # Shipping Line
    shipping_full_description = order.get("shipping_description" or "")
    shipping_amount = order.get("base_shipping_amount", 0)
    if shipping_amount or shipping_full_description:
        shipping_description = shipping_full_description
        shipping_tax_id = env["account.tax"]
        shipping_tax_amount = order.get("base_shipping_tax_amount", 0)
        if shipping_tax_amount and shipping_amount:
            taxes = order["extension_attributes"]["item_applied_taxes"]
            for tax in taxes:
                if tax["type"] == "shipping":
                    shipping_tax_id = env["account.tax"].search(
                        [
                            ("amount", "=", tax["applied_taxes"][0]["percent"]),
                            ("type_tax_use", "=", "sale"),
                            ("company_id", "=", env.company.id),
                        ],
                        limit=1,
                    )
                if tax["type"] == "" and not shipping_tax_id:
                    shipping_tax_id = env["account.tax"].search(
                        [
                            ("amount", "=", tax["applied_taxes"][0]["percent"]),
                            ("type_tax_use", "=", "sale"),
                            ("company_id", "=", env.company.id),
                        ],
                        limit=1,
                    )
            if not shipping_tax_id:
                # No exact match based on %age (common) allow 1% variance
                tax_percent = round(
                    float(order.get("base_shipping_tax_amount", "0"))
                    / order.get("base_shipping_amount", 0)
                    * 100,
                    1,
                )
                shipping_tax_id = env["account.tax"].search(
                    [
                        ("amount", ">", tax_percent - 1),
                        ("amount", "<", tax_percent + 1),
                        ("type_tax_use", "=", "sale"),
                        ("company_id", "=", env.company.id),
                    ],
                    limit=1,
                )
                if not shipping_tax_id:
                    raise EdiException(
                        "Shipping Tax not found:"
                        "\n -Shipping Amount: %s"
                        "\n -Shipping_tax: %s"
                        "\n -Tax Percent: %s"
                        % (shipping_amount, shipping_tax_amount, tax_percent)
                    )
        shipping_product = env["product.product"].search(
            [("name", "=", shipping_description)], limit=1
        )
        if not shipping_product:
            shipping_product = (
                env["product.product"]
                .with_context(skip_edi_push=True)
                .create(
                    {
                        "name": shipping_description,
                        "type": "service",
                        "list_price": order["shipping_amount"],
                        "consignment": False,
                    }
                )
            )
        delivery_carrier = env["delivery.carrier"].search(
            [("name", "=", shipping_description)], limit=1
        )
        if not delivery_carrier and shipping_description:
            delivery_carrier = env["delivery.carrier"].create(
                {
                    "name": shipping_description,
                    "product_id": shipping_product.id,
                    "delivery_type": "fixed",
                    "fixed_price": shipping_amount,
                }
            )
        order_id.write({"carrier_id": delivery_carrier.id})
        order_line = env["sale.order.line"].create(
            {
                "order_id": order_id.odoo_id.id,
                "product_id": shipping_product.id,
                "name": shipping_full_description or "Shipping",
                "product_uom_qty": 1,
                "price_unit": shipping_amount,
                "tax_id": [(6, 0, shipping_tax_id.ids)],
                "is_delivery": True,
            }
        )

    note = order.get("customer_note", "")
    if note:
        order_id.odoo_id.message_post(body=note)

    if order_status not in ["canceled", "cancelled"]:
        if paid or order.get("base_total_due", 0) == 0:
            order_id.action_confirm()
    else:
        order_id.action_cancel()
    order_id.write({"date_order": order["created_at"]})
    record._associate_with(order_id.odoo_id)

    if paid and not order_id.state == "cancel" and order_id.amount_total != 0:
        # Raise Invoice
        move_id = order_id.odoo_id._create_invoices()
        if move_id:
            move_id.write({"invoice_date": order_id.date_order})
            move_id.action_post()
            journal_id = env.ref("connector_edi_magento.edi_magento_journal")
            payment_name = move_id.name
            if payment_method:
                payment_id = order["payment"].get("cc_trans_id", False)
                if payment_id:
                    payment_name = "%s (%s) - %s" % (
                        payment_id,
                        payment_method,
                        payment_name,
                    )
                else:
                    payment_name = "%s - %s" % (payment_method, payment_name)
            env["account.payment.register"].with_context(
                active_model="account.move",
                active_ids=move_id.id,
                default_payment_difference_handling="reconcile",
                default_writeoff_label="Magento Rounding Difference",
                default_writeoff_account_id=journal_id.loss_account_id.id,
            ).create(
                {
                    "payment_date": order_id.date_order,
                    "journal_id": journal_id.id,
                    "amount": paid,
                    "currency_id": move_id.currency_id.id,
                    "communication": payment_name,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": move_id.partner_id.id,
                }
            )._create_payments()"""
