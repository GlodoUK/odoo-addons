from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools import float_compare

CONFORMITY_INTERVAL_TYPE = [
    ("days", "Days"),
    ("weeks", "Weeks"),
    ("months", "Months"),
]


class ProductProduct(models.Model):
    _inherit = "product.product"

    _sql_constraints = [
        (
            "conformity_interval_positive",
            "CHECK(conformity_interval > 0)",
            "The conformity interval must be greater than or equal to 1.",
        ),
        (
            "conformity_quantity_positive",
            "CHECK(conformity_quantity > 0)",
            "The conformity quantity must be greater than or equal to 1.",
        ),
        (
            "conformity_interval_type_required",
            "CHECK(NOT conformity_enabled OR conformity_interval_type IS NOT NULL)",
            "The conformity interval type is required when conformity is enabled.",
        ),
        (
            "conformity_start_date_required",
            "CHECK(NOT conformity_enabled OR conformity_start_date IS NOT NULL)",
            "The conformity start date is required when conformity is enabled.",
        ),
    ]

    conformity_enabled = fields.Boolean()

    conformity_interval = fields.Integer(
        default=1,
    )

    conformity_interval_type = fields.Selection(
        CONFORMITY_INTERVAL_TYPE,
        default="months",
    )

    conformity_start_date = fields.Datetime()

    conformity_end_date = fields.Datetime(
        compute="_compute_conformity_end_date",
        store=True,
    )

    conformity_quantity = fields.Float(
        default=100.0,
    )

    open_conformity_alert_ids = fields.One2many(
        "product.conformity.alert",
        "product_id",
        domain=[("state", "=", "open")],
    )

    open_conformity_alert_count = fields.Integer(
        compute="_compute_open_conformity_alert_count",
    )

    def action_view_conformity_alerts(self):
        self.ensure_one()

        open_alert_ids = self.env["product.conformity.alert"].search(
            [
                ("product_id", "=", self.id),
                ("state", "=", "open"),
            ]
        )

        action = {
            "name": _("Conformity Alerts"),
            "res_model": "product.conformity.alert",
            "type": "ir.actions.act_window",
        }

        if self.open_conformity_alert_count == 1:
            action.update(
                {
                    "res_id": open_alert_ids.id,
                    "view_mode": "form",
                }
            )

        else:
            action.update(
                {
                    "domain": [("id", "in", open_alert_ids.ids)],
                    "view_mode": "tree,form",
                }
            )

        return action

    def toggle_active(self):
        res = super().toggle_active()
        self.filtered(lambda p: p.active).conformity_start_date = fields.Datetime.now()
        return res

    def _compute_open_conformity_alert_count(self):
        grouped_data = self.env["product.conformity.alert"]._read_group(
            [("product_id", "in", self.ids), ("state", "=", "open")],
            groupby=["product_id"],
            aggregates=["__count"],
        )

        mapped_data = {product_id.id: count for product_id, count in grouped_data}

        for product in self:
            product.open_conformity_alert_count = mapped_data.get(product.id, 0)

    @api.depends(
        "conformity_interval", "conformity_interval_type", "conformity_start_date"
    )
    def _compute_conformity_end_date(self):
        for product in self:
            if product.conformity_start_date:
                product.conformity_end_date = (
                    product.conformity_start_date
                    + relativedelta(
                        **{
                            product.conformity_interval_type: product.conformity_interval  # noqa: E501
                        }
                    )
                )
            else:
                product.conformity_end_date = False

    @api.model
    def _cron_conformity(self):
        now = fields.Datetime.now()

        conformity_group_id = self.env.ref(
            "sbs_conformity.group_conformity_alert",
            raise_if_not_found=False,
        )

        conformity_product_ids = self.search(
            [
                ("conformity_enabled", "=", True),
                ("conformity_end_date", "<", now),
            ]
        )

        for product in conformity_product_ids:
            domain = product._conformity_get_done_mrp_production_domain()

            mrp_production_ids = self.env["mrp.production"].search(domain)

            alert_id = self.env["product.conformity.alert"].create(
                {
                    "mrp_production_ids": [(6, 0, mrp_production_ids.ids)],
                    "product_id": product.id,
                    "date_start": product.conformity_start_date,
                    "date_end": product.conformity_end_date,
                    "reason": "time",
                }
            )

            if conformity_group_id:
                alert_id.message_post(
                    body=_("Conformity period expired for %s.", product.display_name),
                    message_type="comment",
                    partner_ids=conformity_group_id.users.partner_id.ids,
                    subtype_xmlid="mail.mt_comment",
                )

            product.conformity_start_date = product.conformity_end_date

    def _check_conformity_quantity(self):
        now = fields.Datetime.now()

        conformity_group_id = self.env.ref(
            "sbs_conformity.group_conformity_alert",
            raise_if_not_found=False,
        )

        conformity_product_ids = self.filtered(lambda p: p.conformity_enabled)

        for product in conformity_product_ids:
            domain = product._conformity_get_done_mrp_production_domain()

            grouped_data = self.env["mrp.production"]._read_group(
                domain,
                ["product_uom_id"],
                ["qty_producing:sum"],
            )

            total_product_qty = 0.0

            for product_uom_id, qty_producing_sum in grouped_data:
                total_product_qty += product_uom_id._compute_quantity(
                    qty_producing_sum,
                    product.uom_id,
                )

            float_comparison = float_compare(
                total_product_qty,
                product.conformity_quantity,
                precision_rounding=product.uom_id.rounding,
            )

            if float_comparison >= 0:
                mrp_production_ids = self.env["mrp.production"].search(domain)

                alert_id = self.env["product.conformity.alert"].create(
                    {
                        "mrp_production_ids": [(6, 0, mrp_production_ids.ids)],
                        "product_id": product.id,
                        "date_start": product.conformity_start_date,
                        "date_end": now,
                        "reason": "quantity",
                    }
                )

                if conformity_group_id:
                    alert_id.message_post(
                        body=_(
                            "Conformity quantity threshold reached for %s.",
                            product.display_name,
                        ),
                        message_type="comment",
                        partner_ids=conformity_group_id.users.partner_id.ids,
                        subtype_xmlid="mail.mt_comment",
                    )

                product.conformity_start_date = now

    def _conformity_get_done_mrp_production_domain(
        self, start_date=False, end_date=False
    ):
        self.ensure_one()

        start_date = start_date or self.conformity_start_date
        end_date = end_date or self.conformity_end_date

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        return [
            ("date_finished", ">=", start_date),
            ("date_finished", "<=", end_date),
            ("state", "=", "done"),
            ("product_id", "=", self.id),
        ]
