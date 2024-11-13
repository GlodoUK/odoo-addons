import binascii
import datetime

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

SPRING_DELIVERY_CODE_MAP = {
    0: "in_transit",
    20: "in_transit",
    21: "in_transit",
    2101: "in_transit",
    25: "unknown",
    31: "incident",
    40: "held",
    41: "incident",
    91: "in_transit",
    92: "held",
    93: "in_transit",
    100: "customer_delivered",
    101: "in_transit",
    111: "incident",
    11101: "incident",
    11102: "incident",
    124: "returned",
    12401: "returned",
    12402: "returned",
    12403: "returned",
    12404: "returned",
    12405: "returned",
    125: "warehouse_delivered",
}


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("spring", "Spring")], ondelete={"spring": "cascade"}
    )

    spring_api_key = fields.Char(string="Spring API Key")
    spring_base_url = fields.Char(default="https://mtapi.net/")
    spring_url = fields.Char(compute="_compute_spring_url", store=True)
    spring_service = fields.Many2one("delivery.spring.service")
    spring_label_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("png", "PNG"),
            ("zpl", "ZPL300"),
            ("zpl2", "ZPL200"),
            ("epl", "EPL"),
        ],
        required=True,
        default="pdf",
    )

    @api.depends("prod_environment")
    def _compute_spring_url(self):
        for record in self:
            if record.delivery_type != "spring":
                continue
            record.spring_url = record.spring_base_url
            if not record.prod_environment:
                record.spring_url += "?testMode=1"

    @api.onchange("delivery_type", "spring_api_key")
    def onchange_delivery_type_spring(self):
        if (
            self.delivery_type == "spring"
            and self.spring_api_key
            and not self.spring_service
        ):
            self.action_spring_get_services()

    def action_spring_get_services(self):
        service_model = self.env["delivery.spring.service"].sudo()

        response = requests.post(
            self.spring_url,
            headers={
                "Content-Type": "text/json",
            },
            json={
                "Apikey": self.spring_api_key,
                "Command": "GetServices",
            },
        )
        services = response.json().get("Services", {})
        service_list = services.get("List", {})
        allowed_services = services.get("AllowedServices", [])

        existing_services = service_model.with_context(active_test=False).search([])

        for existing_service in existing_services:
            if existing_service.ref not in allowed_services:
                existing_service.active = False

        for service in allowed_services:
            existing = existing_services.filtered(
                lambda s, service=service: s.ref == service
            )
            if existing:
                existing.active = True
                continue
            service_model.create(
                {
                    "ref": service,
                    "name": service_list.get(service),
                }
            )

    def spring_rate_shipment(self, order):
        matches = self._match_address(order.partner_shipping_id)
        if not matches:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }

        price = order.pricelist_id.get_product_price(
            self.product_id, 1.0, order.partner_id
        )

        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": _(
                "Spring API does not support dynamic rating at this time"
            ),
        }

    def spring_send_shipping(self, pickings):
        res = []
        for picking in pickings:
            order = picking.sale_id
            product_list = []
            for line in picking.move_lines:
                product_list.append(
                    {
                        "Description": line.name,
                        "Sku": line.product_id.default_code,
                        "OriginCountry": picking.location_id.company_id.country_id.code,
                        "Quantity": line.product_uom_qty,
                        "Value": line.product_id.lst_price,
                        "Weight": line.product_id.weight,
                        "HsCode": line.product_id.hs_code or "",
                    }
                )
            order_value = 0.0
            order_name = picking.name
            order_date = picking.create_date.strftime("%Y-%m-%d")
            if order:
                order_value = order.amount_untaxed
                order_name = order.client_order_ref or order.name
                order_date = order.date_order.strftime("%Y-%m-%d")
            response = requests.post(
                self.spring_url,
                headers={
                    "Content-Type": "text/json",
                },
                json={
                    "Apikey": self.spring_api_key,
                    "Command": "OrderShipment",
                    "Shipment": {
                        "LabelFormat": self.spring_label_format,
                        "ShipperReference": picking.name,
                        "OrderReference": order_name,
                        "OrderDate": order_date,
                        "Service": self.spring_service.ref,
                        "Weight": picking.shipping_weight,
                        "WeightUnit": picking.weight_uom_name,
                        "Value": order_value,
                        "Currency": picking.company_id.currency_id.name,
                        "ConsignorAddress": {
                            "Name": picking.location_id.company_id.name,
                            "Company": picking.location_id.company_id.name,
                        },
                        "ConsigneeAddress": {
                            "Name": picking.partner_id.name,
                            "Company": picking.partner_id.name,
                            "AddressLine1": picking.partner_id.street,
                            "AddressLine2": picking.partner_id.street2,
                            "City": picking.partner_id.city,
                            "State": picking.partner_id.state_id.name,
                            "Zip": picking.partner_id.zip,
                            "Country": picking.partner_id.country_id.code or "",
                            "Phone": picking.partner_id.phone,
                            "Email": picking.partner_id.email,
                            "Vat": picking.partner_id.vat,
                        },
                        "Products": product_list,
                    },
                },
            )
            if not response:
                raise ValidationError(_("Unknown Spring API Error"))

            json = response.json()

            if json.get("ErrorLevel") != 0:
                raise ValidationError(_("Spring API Error: %s") % json.get("Error"))

            shipment = json.get("Shipment")
            tracking = shipment.get("TrackingNumber")
            tracking_url = shipment.get("CarrierTrackingUrl")
            attachments_list = None

            if shipment.get("LabelImage"):
                attachments_list = [
                    (
                        "Spring_{tracking}.{label_fmt}".format(
                            tracking=str(tracking),
                            label_fmt=self.spring_label_format.replace("2", ""),
                        ),
                        binascii.a2b_base64(str(shipment.get("LabelImage"))),
                    )
                ]

            picking.message_post(
                body=_(
                    "Shipment sent to Spring<br/>"
                    "Carrier: %(carrier_name)s<br/>"
                    "Tracking Number: %(tracking_ref)s<br/>"
                    "Tracking URL: %(url)s"
                )
                % {
                    "carrier_name": shipment.get("Carrier"),
                    "tracking_ref": tracking,
                    "url": tracking_url,
                },
                attachments=attachments_list,
            )

            picking.write(
                {
                    "carrier_consignment_ref": picking.name,
                    "spring_carrier": shipment.get("Carrier"),
                    "spring_tracking_url": tracking_url,
                }
            )
            self.spring_tracking_state_update(picking)

            res.append(
                {
                    "exact_price": 0.0,
                    "tracking_number": tracking,
                    "date_delivery": fields.Date.today(),
                    "weight": picking.shipping_weight,
                }
            )

        return res

    def spring_cancel_shipment(self, pickings):
        for picking in pickings:
            response = requests.post(
                self.spring_url,
                headers={
                    "Content-Type": "text/json",
                },
                json={
                    "Apikey": self.spring_api_key,
                    "Command": "VoidShipment",
                    "Shipment": {
                        "ShipperReference": picking.name,
                    },
                },
            )
            if not response:
                raise ValidationError(_("Unknown Spring API Error"))

            json = response.json()

            if json.get("ErrorLevel") != 0:
                raise ValidationError(_("Spring API Error: %s") % json.get("Error"))
            picking.carrier_tracking_url = False

    def spring_tracking_state_update_scheduled(self):
        pickings = self.env["stock.picking"].search(
            [
                ("carrier_id", "=", self.id),
                ("state", "=", "done"),
                (
                    "delivery_state",
                    "not in",
                    ["customer_delivered", "warehouse_delivered"],
                ),
                ("date_next_tracking_update", "<=", fields.datetime.now()),
                "|",
                ("carrier_consignment_ref", "!=", False),
                ("carrier_tracking_ref", "!=", False),
            ]
        )
        for picking in pickings:
            if picking.delivery_state in ["customer_delivered", "warehouse_delivered"]:
                continue
            self.spring_tracking_state_update(picking)

    def spring_tracking_state_update(self, picking):
        response = requests.post(
            self.spring_url,
            headers={
                "Content-Type": "text/json",
            },
            json={
                "Apikey": self.spring_api_key,
                "Command": "TrackShipment",
                "Shipment": {
                    "ShipperReference": picking.name,
                },
            },
        )
        if not response:
            raise ValidationError(_("Unknown Spring API Error"))

        json = response.json()

        if json.get("ErrorLevel") != 0:
            picking.message_post(body=_("Spring API Error: %s") % json.get("Error"))

        shipment = json.get("Shipment", {})
        events = sorted(shipment.get("Events", []), key=lambda e: e.get("DateTime"))
        if len(events) > picking.tracking_history_count:
            for index, event in enumerate(events):
                if index > picking.tracking_history_count - 1:
                    self.env["stock.picking.tracking.history"].create(
                        {
                            "picking_id": picking.id,
                            "date_event": event.get("DateTime"),
                            "description": (
                                "{code}: {desc} ({carrier_code}, {carrier_desc})"
                            ).format(
                                code=event.get("Code"),
                                desc=event.get("Description"),
                                carrier_code=event.get("CarrierCode"),
                                carrier_desc=event.get("CarrierDescription"),
                            ),
                        }
                    )
            latest_event = events[-1]
            current_state = SPRING_DELIVERY_CODE_MAP.get(latest_event.get("Code"))
            if not current_state:
                picking.delivery_state = "unknown"
            else:
                picking.delivery_state = current_state
                picking.tracking_state = (
                    "{code}: {desc} ({carrier_code}, {carrier_desc})"
                ).format(
                    code=latest_event.get("Code"),
                    desc=latest_event.get("Description"),
                    carrier_code=latest_event.get("CarrierCode"),
                    carrier_desc=latest_event.get("CarrierDescription"),
                )
            if current_state in ["customer_delivered", "warehouse_delivered"]:
                picking.date_delivered = latest_event.get("DateTime")

    def spring_tracking_state_calc_next_update(self, picking):
        if picking.delivery_state in ["customer_delivered", "warehouse_delivered"]:
            return False
        return fields.datetime.now() + datetime.timedelta(hours=4)

    def spring_get_tracking_link(self, picking):
        return picking.spring_tracking_url


class SpringService(models.Model):
    _name = "delivery.spring.service"
    _description = "Spring Service"

    active = fields.Boolean(default=True)
    name = fields.Char()
    ref = fields.Char()
