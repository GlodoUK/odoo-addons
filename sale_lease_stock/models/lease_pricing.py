from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

PERIODS = [
    ("hours", "Hours"),
    ("days", "Days"),
    ("weeks", "Weeks"),
    ("months", "Months"),
    ("years", "Years"),
]


class LeasePricing(models.Model):
    """Sale Lease pricing rules."""

    _name = "sale_lease_stock.pricing"
    _description = "Leasing Pricing Rule"
    _order = "price"

    duration = fields.Integer(
        string="Duration",
        required=True,
        default=12,
    )
    unit = fields.Selection(
        PERIODS,
        string="Unit",
        required=True,
        default="months",
    )

    price = fields.Monetary(
        string="Price",
        required=True,
        default=1.0,
    )
    currency_id = fields.Many2one(
        "res.currency",
        "Currency",
        default=lambda self: self.env.company.currency_id.id,
        required=True,
    )

    product_template_id = fields.Many2one(
        "product.template",
        string="Product Templates",
        help="Select products on which this pricing will be applied.",
    )

    product_variant_ids = fields.Many2many(
        "product.product",
        string="Product Variants",
        help="Select Variants of the Product for which this rule applies."
        "\n Leave empty if this rule applies for any variant of this template.",
    )
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist")
    company_id = fields.Many2one("res.company", related="pricelist_id.company_id")

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id(self):
        for pricing in self.filtered("pricelist_id"):
            pricing.currency_id = pricing.pricelist_id.currency_id

    def name_get(self):
        result = []
        uom_translation = dict()
        for key, value in self._fields["unit"]._description_selection(self.env):
            uom_translation[key] = value
        for pricing in self:
            label = _("Lease: %d %s") % (
                pricing.duration,
                uom_translation[pricing.unit],
            )
            result.append((pricing.id, label))
        return result

    def _compute_end_date(self, start_date):
        self.ensure_one()

        kwargs = {
            self.unit: self.duration,
        }

        return start_date + relativedelta(**kwargs)

    def _get_total_price(self):
        self.ensure_one()
        return self.price * self.duration

    def applies_to(self, product):
        return self.product_template_id == product.product_tmpl_id and (
            not self.product_variant_ids or product in self.product_variant_ids
        )

    _sql_constraints = [
        (
            "lease_pricing_duration",
            "CHECK(duration >= 0)",
            "The pricing duration has to be greater or equal to 0.",
        ),
        (
            "lease_pricing_price",
            "CHECK(price >= 0)",
            "The pricing price has to be greater or equal to 0.",
        ),
    ]
