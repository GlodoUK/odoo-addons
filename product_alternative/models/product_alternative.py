from ast import literal_eval

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductAlternative(models.Model):
    """Directional link declaring that ``product_tmpl_id`` has an alternative.

    Both ends are scoped with a domain over ``product.product`` instead of a
    fixed variant, which keeps a single, flexible mechanism:

    * ``product_domain`` selects which variants of the *source* product the
      link applies to (empty = every variant);
    * ``alternative_domain`` narrows which variants of ``alternative_tmpl_id``
      are proposed (empty = every variant).

    A domain subsumes every granularity we need: ``[('id', '=', N)]`` pins one
    specific variant, ``[]`` means the whole template, and attribute/category/
    price filters express everything in between. Because alternatives are
    resolved through ``search``/``filtered_domain`` (which only ever return
    materialised, active records), the link stays valid for templates using
    dynamic variants without ever forcing a variant to be created.
    """

    _name = "product.alternative"
    _description = "Product Alternative Rule"
    _inherit = ["mail.thread"]
    _order = "sequence, id"
    _check_company_auto = True

    active = fields.Boolean(default=True, index=True)
    sequence = fields.Integer(default=10, index=True)
    # Defaults to 'domain' so existing records (and Odoo's backfill of this
    # column onto them) keep their current domain behaviour.
    mode = fields.Selection(
        [("domain", "Domain"), ("specific", "Simple")],
        required=True,
        default="specific",
        help="Domain: scope each side with a product domain. "
        "Specific: link the templates directly, optionally pinning a single "
        "variant on either side.",
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product",
        required=True,
        ondelete="cascade",
        index=True,
        help="Product this alternative is declared on.",
        tracking=True,
        check_company=True,
    )
    product_domain = fields.Char(
        string="Applies To Domain",
        default="[]",
        help="Domain on product variants selecting which variants of this "
        "product the alternative applies to. Leave empty to apply to "
        "every variant. Used in Domain mode.",
        tracking=True,
    )
    product_variant_ids = fields.Many2many(
        "product.product",
        relation="product_alternative_source_variant_rel",
        column1="alternative_id",
        column2="product_id",
        string="Product Variants",
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help="In Specific mode, restrict the link to these source variants. "
        "Leave empty to apply to every variant of the product.",
        tracking=True,
    )
    alternative_tmpl_id = fields.Many2one(
        "product.template",
        string="Alternative Product",
        ondelete="cascade",
        index=True,
        help="Product proposed as an alternative. Used in Specific mode only; "
        "in Domain mode the alternatives are defined entirely by the domain, "
        "which can match variants of any product.",
        tracking=True,
        check_company=True,
    )
    alternative_domain = fields.Char(
        string="Alternative Variant Domain",
        default="[]",
        help="Domain on product variants selecting which variants are "
        "proposed as alternatives, matched across all products. Used in "
        "Domain mode. Leave empty to propose every variant of every product.",
        tracking=True,
    )
    alternative_variant_ids = fields.Many2many(
        "product.product",
        relation="product_alternative_target_variant_rel",
        column1="alternative_id",
        column2="product_id",
        string="Alternative Variants",
        domain="[('product_tmpl_id', '=', alternative_tmpl_id)]",
        help="In Specific mode, propose only these variants of the "
        "alternative. Leave empty to propose every variant.",
        tracking=True,
    )
    note = fields.Char()
    company_id = fields.Many2one(
        related="product_tmpl_id.company_id",
        store=True,
        index=True,
    )
    matched_variant_count = fields.Integer(
        string="# Variants",
        compute="_compute_matched_variant_count",
        help="How many variants of the alternative product currently match.",
        store=True,
    )

    @api.depends(
        "mode",
        "alternative_tmpl_id",
        "alternative_domain",
        "alternative_variant_ids",
    )
    def _compute_matched_variant_count(self):
        for alternative in self:
            alternative.matched_variant_count = len(
                alternative._get_alternative_variants()
            )

    @api.onchange("mode")
    def _onchange_mode(self):
        # In domain mode the alternative is expressed purely through the
        # domain, so the template-based fields must not be filled in.
        if self.mode == "domain":
            self.alternative_tmpl_id = False
            self.alternative_variant_ids = False
            self.product_variant_ids = False

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        self.product_variant_ids = self.product_variant_ids.filtered(
            lambda v: v.product_tmpl_id == self.product_tmpl_id
        )

    @api.onchange("alternative_tmpl_id")
    def _onchange_alternative_tmpl_id(self):
        self.alternative_variant_ids = self.alternative_variant_ids.filtered(
            lambda v: v.product_tmpl_id == self.alternative_tmpl_id
        )

    @api.constrains("product_tmpl_id", "alternative_tmpl_id")
    def _check_not_self(self):
        for alternative in self:
            if alternative.product_tmpl_id == alternative.alternative_tmpl_id:
                raise ValidationError(
                    self.env._("A product cannot be an alternative of itself.")
                )

    @api.constrains("mode", "alternative_tmpl_id")
    def _check_alternative_template(self):
        for alternative in self:
            if alternative.mode == "specific" and not alternative.alternative_tmpl_id:
                raise ValidationError(
                    self.env._("An alternative product is required in Specific mode.")
                )
            if alternative.mode == "domain" and alternative.alternative_tmpl_id:
                raise ValidationError(
                    self.env._(
                        "In Domain mode the alternatives are defined by the "
                        "domain; leave the alternative product empty."
                    )
                )

    @api.constrains("product_variant_ids", "product_tmpl_id")
    def _check_product_variants(self):
        for alternative in self:
            if (
                alternative.product_variant_ids.product_tmpl_id
                - alternative.product_tmpl_id
            ):
                raise ValidationError(
                    self.env._("The source variants must belong to the product.")
                )

    @api.constrains("alternative_variant_ids", "alternative_tmpl_id")
    def _check_alternative_variants(self):
        for alternative in self:
            if (
                alternative.alternative_variant_ids.product_tmpl_id
                - alternative.alternative_tmpl_id
            ):
                raise ValidationError(
                    self.env._(
                        "The alternative variants must belong to the alternative"
                        " product."
                    )
                )

    def _matches_source_variant(self, variant):
        """Whether ``variant`` (of the source product) is in this link's scope."""
        self.ensure_one()
        if self.mode == "specific":
            # Pinned variants, or every variant of the source product.
            return not self.product_variant_ids or variant in self.product_variant_ids
        return bool(variant.filtered_domain(literal_eval(self.product_domain)))

    def _get_alternative_variants(self):
        """Resolve to currently-materialised ``product.product`` alternatives,
        ignoring source-side scoping.

        In domain mode the resolution runs through ``search``, which only
        returns materialised, active records, so dynamic templates yield only
        variants that already exist (never created speculatively). The domain
        is matched across every product (it is not bound to a template), so
        any leaf restricting the template must be part of the domain itself.
        """
        variants = self.env["product.product"]
        for alternative in self:
            if alternative.mode == "specific":
                if not alternative.alternative_tmpl_id:
                    continue
                # Pinned variants, or every materialised variant of the target.
                variants |= (
                    alternative.alternative_variant_ids
                    or alternative.alternative_tmpl_id.product_variant_ids
                )
                continue
            domain = literal_eval(alternative.alternative_domain)
            variants |= self.env["product.product"].search(domain)
        return variants
