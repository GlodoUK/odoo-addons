from collections import defaultdict

from odoo import api, fields, models

from .product_product import CONFORMITY_INTERVAL_TYPE


class ProductTemplate(models.Model):
    _inherit = "product.template"

    conformity_enabled = fields.Boolean(
        compute="_compute_conformity_enabled",
        inverse="_inverse_conformity_enabled",
    )

    conformity_interval = fields.Integer(
        compute="_compute_conformity_interval",
        inverse="_inverse_conformity_interval",
    )

    conformity_interval_type = fields.Selection(
        CONFORMITY_INTERVAL_TYPE,
        compute="_compute_conformity_interval_type",
        inverse="_inverse_conformity_interval_type",
    )

    conformity_start_date = fields.Datetime(
        compute="_compute_conformity_start_date",
        inverse="_inverse_conformity_start_date",
    )

    conformity_end_date = fields.Datetime(
        compute="_compute_conformity_end_date",
    )

    conformity_quantity = fields.Float(
        compute="_compute_conformity_quantity",
        inverse="_inverse_conformity_quantity",
    )

    open_conformity_alert_ids = fields.One2many(
        "product.conformity.alert",
        "product_tmpl_id",
        domain=[("state", "=", "open")],
    )

    open_conformity_alert_count = fields.Integer(
        compute="_compute_conformity_alert_count",
    )

    def action_view_conformity_alerts(self):
        self.ensure_one()

        open_alert_ids = self.env["product.conformity.alert"].search(
            [
                ("product_id", "in", self.product_variant_ids.ids),
                ("state", "=", "open"),
            ]
        )

        action = {
            "name": self.env._("Conformity Alerts"),
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
                    "view_mode": "list,form",
                }
            )

        return action

    def _compute_conformity_alert_count(self):
        grouped_data = self.env["product.conformity.alert"]._read_group(
            [
                ("product_id", "in", self.product_variant_ids.ids),
                ("state", "=", "open"),
            ],
            groupby=["product_id"],
            aggregates=["__count"],
        )

        product_tmpl_count = defaultdict(int)

        for product_id, count in grouped_data:
            product_tmpl_count[product_id.product_tmpl_id.id] += count

        for template in self:
            template.open_conformity_alert_count = product_tmpl_count.get(
                template.id, 0
            )

    @api.depends("product_variant_ids.conformity_enabled")
    def _compute_conformity_enabled(self):
        self._compute_template_field_from_variant_field("conformity_enabled")

    def _inverse_conformity_enabled(self):
        self._set_product_variant_field("conformity_enabled")

    @api.depends("product_variant_ids.conformity_interval")
    def _compute_conformity_interval(self):
        self._compute_template_field_from_variant_field(
            "conformity_interval",
            default=1,
        )

    def _inverse_conformity_interval(self):
        self._set_product_variant_field("conformity_interval")

    @api.depends("product_variant_ids.conformity_interval_type")
    def _compute_conformity_interval_type(self):
        self._compute_template_field_from_variant_field(
            "conformity_interval_type",
            default="months",
        )

    def _inverse_conformity_interval_type(self):
        self._set_product_variant_field("conformity_interval_type")

    @api.depends("product_variant_ids.conformity_start_date")
    def _compute_conformity_start_date(self):
        self._compute_template_field_from_variant_field(
            "conformity_start_date",
        )

    def _inverse_conformity_start_date(self):
        self._set_product_variant_field(
            "conformity_start_date",
        )

    @api.depends("product_variant_ids.conformity_quantity")
    def _compute_conformity_quantity(self):
        self._compute_template_field_from_variant_field(
            "conformity_quantity",
            default=100.0,
        )

    def _inverse_conformity_quantity(self):
        self._set_product_variant_field(
            "conformity_quantity",
        )

    @api.depends("product_variant_ids.conformity_end_date")
    def _compute_conformity_end_date(self):
        self._compute_template_field_from_variant_field("conformity_end_date")
