import datetime

from odoo import fields, models
from odoo.osv import expression


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    ref = fields.Char(string="Internal Reference")
    tracking_smart_button = fields.Boolean(
        string="Display Carrier Tracking Smart Button on Pickings",
        default=True,
    )

    def tracking_state_update_scheduled_picking_domain(self):
        self.ensure_one()

        return expression.AND(
            [
                [
                    (
                        "create_date",
                        ">=",
                        fields.Datetime.now() - datetime.timedelta(weeks=8),
                    ),
                    ("carrier_id", "=", self.id),
                    (
                        "delivery_state",
                        "in",
                        [
                            False,
                            "",
                            "unknown",
                            "shipping_recorded_in_carrier",
                            "in_transit",
                            "incident",
                            "held",
                        ],
                    ),
                ],
                expression.OR(
                    [
                        [("date_next_tracking_update", "<=", fields.Datetime.now())],
                        [("date_next_tracking_update", "=", False)],
                    ]
                ),
            ]
        )

    def tracking_state_update_scheduled(self):
        """
        Poll the tracking history using a schedule.
        This can be used for 2 features:
        1. Periodically finding and polling for all outstanding deliveries
        2. Some carriers may only support signatures, etc. through file drops

        It is the responsibility of each carrier implementation to determine how
        they wish to implement this.
        """

        for record in self:
            method_name = "%s_tracking_state_update_scheduled" % (record.delivery_type)

            if not hasattr(record, method_name):
                continue

            getattr(record, method_name)()

    def tracking_state_calc_next_update(self, picking):
        """
        Delegate the calculation of the next tracking update to the carrier
        """
        if not picking:
            return False

        self.ensure_one()
        picking.ensure_one()

        method_name = "%s_tracking_state_calc_next_update" % (self.delivery_type)

        if not hasattr(self, method_name):
            return False

        return getattr(self, method_name)(picking)

    def tracking_state_update(self, picking):
        """
        Poll the carrier for a specific picking, if possible.
        """
        self.ensure_one()

        if not picking:
            return

        picking.ensure_one()
        method_name = "%s_tracking_state_update" % (self.delivery_type)

        if not hasattr(self, method_name):
            return

        getattr(self, method_name)(picking)

        picking.write(
            {
                "date_next_tracking_update": self.tracking_state_calc_next_update(
                    picking
                ),
            }
        )
