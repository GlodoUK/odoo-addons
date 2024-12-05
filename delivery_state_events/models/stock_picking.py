from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_consignment_ref = fields.Char(
        string="Consignment Reference",
        help="The consignment reference is not necessarily the same as the"
        "carrier_tracking_ref. This will typically be the stock.picking name,"
        "but does not necessarily need to be.",
    )
    tracking_history_ids = fields.One2many(
        "stock.picking.tracking.history", "picking_id", auto_join=True
    )
    tracking_history_count = fields.Integer(
        compute="_compute_tracking_history_count",
        store=True,
    )
    tracking_signature_ids = fields.One2many(
        "stock.picking.tracking.signature", "picking_id", auto_join=True
    )
    tracking_signature_count = fields.Integer(
        compute="_compute_tracking_signature_count",
        store=True,
    )
    date_shipped = fields.Date(string="Ship Date", readonly=True, index=True)
    date_delivered = fields.Datetime(
        string="Delivery Date",
        readonly=True,
    )
    tracking_state = fields.Char(
        string="Carrier State",
        readonly=True,
        index=True,
        tracking=True,
        help="Carrier's Raw Tracking State",
    )
    delivery_state = fields.Selection(
        selection=[
            ("shipping_recorded_in_carrier", "Shipping Recorded in Carrier"),
            ("in_transit", "In Transit"),
            ("cancelled_shipment", "Cancelled"),
            ("incident", "Incident"),
            ("customer_delivered", "Delivered (Customer)"),
            ("warehouse_delivered", "Delivered (Warehouse)"),
            ("rejected", "Rejected"),
            ("returned", "Returned to Sender"),
            ("held", "Held"),
            ("unknown", "Unknown Carrier Reference"),
        ],
        tracking=True,
        readonly=True,
    )
    date_next_tracking_update = fields.Datetime()
    show_open_website_url = fields.Boolean(compute="_compute_show_open_website_url")

    @api.depends("carrier_id", "carrier_tracking_ref")
    def _compute_show_open_website_url(self):
        for picking in self:
            if not picking.carrier_id.tracking_smart_button:
                picking.show_open_website_url = False
                continue

            if picking.carrier_id.delivery_type == "grid":
                picking.show_open_website_url = False
                continue

            if not picking.carrier_tracking_url:
                picking.show_open_website_url = False
                continue

            picking.show_open_website_url = True

    @api.depends("tracking_history_ids")
    def _compute_tracking_history_count(self):
        for picking in self:
            picking.tracking_history_count = len(picking.tracking_history_ids)

    @api.depends("tracking_signature_ids")
    def _compute_tracking_signature_count(self):
        for picking in self:
            picking.tracking_signature_count = len(picking.tracking_signature_ids)

    def tracking_state_update(self):
        """
        Query the carrier for tracking update information, if possible
        """
        for picking in self.filtered("carrier_id"):
            picking.carrier_id.tracking_state_update(picking)

    def _action_done(self):
        res = super()._action_done()

        for record in self.filtered(lambda p: p.carrier_id):
            record.date_next_tracking_update = (
                record.carrier_id.tracking_state_calc_next_update(record)
            )

        return res
