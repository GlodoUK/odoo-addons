import copy

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import (
    format_amount,
    format_date,
    format_datetime,
    format_duration,
    format_time,
    is_html_empty,
)
from odoo.tools.rendering_tools import (
    parse_inline_template,
    render_inline_template,
    template_env_globals,
)
from odoo.tools.safe_eval import safe_eval

DEFAULT_CPQ_REF_CODE = """# Available variables:
#   record: The current product.product which has been created
#   tmpl: The current product.template
#
# Output:
#   ref: Set with what you want for your end variant internal reference

ref = ""
"""


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cpq_ok = fields.Boolean(string="Configurable Product?")
    cpq_ref = fields.Char(
        string="Configurable Internal Reference",
        index=True,
        help="Reference for this configurable template",
    )
    cpq_ref_mode = fields.Selection(
        [
            ("none", "No"),
            ("inline", "Using Inline QWeb"),
            ("code", "Using Python Code"),
        ],
        default="inline",
        required=True,
        string="Dynamic Configurable Variant Internal Reference",
    )
    cpq_ref_tmpl = fields.Text(
        string="Configurable Internal Reference Inline QWeb Template",
        help="Inline QWeb Template for generating dynamic variant internal reference",
    )
    cpq_ref_code = fields.Text(
        default=DEFAULT_CPQ_REF_CODE,
        string="Configurable Internal Reference using Python Code",
        help="Code for generating dynamic variant internal reference",
    )
    cpq_tooltip = fields.Html(compute="_compute_cpq_tooltip")

    @api.model
    def _name_search(self, name, args=None, operator="ilike", limit=100, order=None):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("cpq_ref", operator, name), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        return super()._name_search(
            name, expression.AND([domain, args]), operator, limit, order
        )

    def _cpq_tooltip_items(self):
        self.ensure_one()
        return [
            _("Configurable Products will generate their product variants on demand."),
            _(
                "Configurable Products allow for custom inputs to be \
                    propagated through the system."
            ),
        ]

    @api.depends("cpq_ok")
    def _compute_cpq_tooltip(self):
        for record in self:
            if not record.cpq_ok:
                record.cpq_tooltip = False
                continue
            record.cpq_tooltip = "".join(
                [f"<p>{i}</p>" for i in self._cpq_tooltip_items()]
            )

    @api.depends("product_variant_ids.product_tmpl_id")
    def _compute_product_variant_count(self):
        """
        For cpq products return the number of variants configured or at least 1.

        Many views and methods trigger only when a template has at least
        one variant attached, and need them to function appropriately.
        """
        res = super()._compute_product_variant_count()
        for record in self.filtered(lambda p: p.cpq_ok and not p.product_variant_ids):
            record.product_variant_count = 1
        return res

    @api.depends("cpq_ok", "product_variant_ids", "product_variant_ids.default_code")
    def _compute_default_code(self):
        todo = self
        for record in self.filtered(lambda r: r.cpq_ok):
            record.default_code = False
            todo -= record
        return super(ProductTemplate, todo)._compute_default_code()

    def _set_default_code(self):
        return super(
            ProductTemplate, self.filtered(lambda r: not r.cpq_ok)
        )._set_default_code()

    def _onchange_cpq_ok_warning_msg(self):
        self.ensure_one()

        return [
            "Switching a product to/from configurable when there are"
            " pre-existing variants will almost certainly have an unexpected"
            " outcome. ",
            "It is suggested either to archive the existing"
            " product and create a new one, or archive/delete all"
            " existing variants, unless you are 100%"
            " sure that you are not introducing incompatibilities"
            " into the system.",
        ]

    @api.onchange("cpq_ok")
    def _onchange_cpq_ok(self):
        if not self._origin:
            return

        if self._origin.cpq_ok != self.cpq_ok and self.product_variant_ids:
            return {
                "warning": {
                    "title": _("Changing Configurable is Dangerous"),
                    "message": _("\n\n".join(self._onchange_cpq_ok_warning_msg())),
                }
            }

    def toggle_cpq(self):
        for record in self:
            record.cpq_ok = not record.cpq_ok

    def configure_cpq_dialog(self):
        self.ensure_one()

        return {
            "name": "CPQ Dialog",
            "type": "ir.actions.client",
            "tag": "cpq.ConfigureDialogAction",
            "target": "self",
        }

    def _create_variant_ids(self):
        """
        Prevent cpq products from creating variants as these serve
        only as a template for the product configurator
        """
        templates = self.filtered(lambda t: not t.cpq_ok)
        if not templates:
            return None
        return super(ProductTemplate, templates)._create_variant_ids()

    def _cpq_get_create_variant_vals(self, pta_value_ids, custom_dict=None):
        self.ensure_one()

        cpq_custom_values = []

        if not custom_dict:
            custom_dict = {}

        for ptav_id, value in custom_dict.items():
            cpq_custom_values.append(
                (
                    0,
                    0,
                    {
                        "ptav_id": ptav_id.id,
                        "custom_value": value,
                    },
                )
            )

        vals = {
            "product_tmpl_id": self.id,
            "product_template_attribute_value_ids": [(6, 0, pta_value_ids.ids)],
            "cpq_custom_value_ids": cpq_custom_values or False,
        }

        return vals

    # flake8: noqa: C901
    def _cpq_ensure_valid_values(
        self,
        ptav_ids,
        custom_dict,
        raise_on_invalidity=True,
        validate_only=False,
    ):
        # ensure that the values passed in are valid, and then extract out the
        # data that we need to find any existing products, and also to validate
        # and sanitise the inputs
        self.ensure_one()

        errors = []

        if not self.cpq_ok:
            msg = _("%s is not a CPQ Enabled Product!") % (self.display_name)
            if raise_on_invalidity:
                raise UserError(msg)
            return (False, msg)

        if not ptav_ids:
            msg = _(
                "%s could not be configured - did not receive any product"
                "template attribute values!"
            ) % (self.display_name)
            if raise_on_invalidity:
                raise UserError(msg)
            return (False, msg)

        errors = {}

        # search_domain to help find an existing attribute
        search_domain = [
            ("product_tmpl_id", "=", self.id),
            ("cpq_ok", "=", True),
        ]

        combination_ptav_ids = self.env["product.template.attribute.value"]
        matched_ptav_ids = self.env["product.template.attribute.value"]
        matched_custom_ptav_ids = self.env["product.template.attribute.value"]
        matched_custom_dict = {}

        valid_product_tmpl_ptav_ids = (
            self.valid_product_template_attribute_line_ids.mapped(
                "product_template_value_ids"
            )
        )

        for ptav_id in ptav_ids:
            if not self.env.context.get("skip_cpq_validate_ptav_ids"):
                # we allow this to be disabled for CoGs explosions
                if ptav_id not in valid_product_tmpl_ptav_ids:
                    msg = _(
                        "Unknown product template attribute value %(key)s for %(tmpl)s"
                    ) % {
                        "key": ptav_id,
                        "tmpl": self.display_name,
                    }

                    if raise_on_invalidity:
                        raise UserError(msg)
                    errors[ptav_id.id] = msg
                    continue

            # we need to pass all ptavs to _is_combination_possible_by_config,
            # even if we're ignoring them
            combination_ptav_ids |= ptav_id

            if not ptav_id.attribute_id.cpq_propagate_to_variant:
                # if it's not supposed to propagate, skip
                continue

            if ptav_id in matched_ptav_ids:
                # have we seen this more than once when we should not have?
                msg = _("%s - product template attribute value seen multiple times") % (
                    self
                )
                if raise_on_invalidity:
                    raise UserError(msg)
                errors[ptav_id.id] = msg
                continue

            matched_ptav_ids |= ptav_id

            if ptav_id.product_attribute_value_id.is_custom:
                if not self.env.context.get(
                    "skip_cpq_validate_ptav_ids"
                ) and not ptav_id.product_attribute_value_id._cpq_validate_custom(
                    custom_dict.get(ptav_id)
                ):
                    msg = _("Custom value '%(name)s' invalid: '%(value)s'") % {
                        "name": ptav_id.display_name,
                        "value": custom_dict.get(ptav_id),
                    }
                    if raise_on_invalidity:
                        raise UserError(msg)
                    errors[ptav_id.id] = msg
                    continue

                matched_custom_ptav_ids |= ptav_id
                matched_custom_dict[
                    ptav_id
                ] = ptav_id.product_attribute_value_id._cpq_sanitise_custom(
                    custom_dict.get(ptav_id)
                )

        is_possible = self._is_combination_possible_by_config(
            combination=combination_ptav_ids,
            ignore_no_variant=True,
        )

        if not is_possible and not self.env.context.get("skip_cpq_validate_ptav_ids"):
            is_possible_ptals = self.valid_product_template_attribute_line_ids._without_no_variant_attributes()  # noqa: E501

            extra_info = _("Likely exclusion is configured. Please check.")

            if len(combination_ptav_ids) != len(is_possible_ptals):
                extra_info = _(
                    "Missing configuration options. Found %(found)s,"
                    " expected %(expected)s. "
                ) % {
                    "found": len(combination_ptav_ids),
                    "expected": len(is_possible_ptals),
                }

                is_possible_ptals_missing_ids = (
                    is_possible_ptals - combination_ptav_ids.attribute_line_id
                )
                if is_possible_ptals_missing_ids:
                    extra_info += _("Suspected missing options: %(suspected)s ") % {
                        "suspected": ", ".join(
                            is_possible_ptals_missing_ids.mapped("display_name")
                        )
                    }

            msg = _(
                "%(tmpl_name)s configuration is not possible by configuration.\n"
                "Using configuration: %(configuration)s\n"
                "%(extra_info)s\n"
                "If this is not on your order or configuration, \
                    please check the configuration of any child items."
            ) % {
                "tmpl_name": self.display_name,
                "configuration": ", ".join(combination_ptav_ids.mapped("display_name")),
                "extra_info": extra_info or "",
            }
            if raise_on_invalidity:
                raise UserError(msg)

        if validate_only:
            if errors:
                return (False, errors)
            return (True, "")

        cpq_custom_combination_indices = ""
        cpq_combination_indices = matched_ptav_ids._ids2str()

        search_domain.append(("cpq_combination_indices", "=", cpq_combination_indices))

        if matched_custom_ptav_ids:
            cpq_custom_combination_indices = ",".join(
                sorted(
                    matched_custom_ptav_ids.mapped(
                        lambda ptav_id: self.env[
                            "product.product.cpq.custom.value"
                        ]._generate_hash(ptav_id, matched_custom_dict.get(ptav_id))
                    )
                )
            )

        search_domain.append(
            ("cpq_custom_combination_indices", "=", cpq_custom_combination_indices)
        )

        return (
            search_domain,
            matched_custom_dict,
            matched_ptav_ids,
            cpq_combination_indices,
            cpq_custom_combination_indices,
        )

    def _cpq_get_create_variant(self, ptav_ids, custom_dict):
        self.ensure_one()
        (
            search_domain,
            matched_custom_dict,
            matched_ptav_ids,
            cpq_combination_indices,
            cpq_custom_combination_indices,
        ) = self._cpq_ensure_valid_values(ptav_ids, custom_dict)

        variant_ids = self.env["product.product"].search(search_domain)

        if variant_ids:
            variant_id = fields.first(variant_ids)
            return self._cpq_get_create_variant_post_find_hook(variant_id)

        variant_id = (
            self.env["product.product"]
            .sudo()
            .with_context(mail_create_nolog=True)
            .create(
                self._cpq_get_create_variant_vals(matched_ptav_ids, matched_custom_dict)
            )
        )
        variant_id = self._cpq_get_create_variant_post_create_hook(variant_id)
        variant_id.message_post(
            body=_("Product created via CPQ wizard"),
            author_id=self.env.user.partner_id.id,
        )
        if variant_id.cpq_combination_indices != cpq_combination_indices:
            raise ValidationError(
                _(
                    "Possible programming error, cpq_combination_indices"
                    " mismatch. Found %(found)s, expected %(expected)s"
                )
                % {
                    "found": variant_id.cpq_combination_indices,
                    "expected": cpq_combination_indices,
                }
            )

        if variant_id.cpq_custom_combination_indices != cpq_custom_combination_indices:
            raise ValidationError(
                _(
                    "Possible programming error, cpq_custom_combination_indices"
                    " mismatch. Found %(found)s, expected %(expected)s"
                )
                % {
                    "found": variant_id.cpq_custom_combination_indices,
                    "expected": cpq_custom_combination_indices,
                }
            )

        return variant_id

    def _cpq_get_create_variant_post_find_hook(self, variant_id):
        return variant_id

    def _cpq_get_variant_ref(self, variant_id):
        self.ensure_one()
        if self.cpq_ref_mode == "none":
            return False

        if self.cpq_ref_mode == "inline":
            return self._cpq_render_inline_template(
                self.cpq_ref_tmpl,
                extras={
                    "record": variant_id,
                    "tmpl": self,
                },
            )

        if self.cpq_ref_mode == "code" and self.cpq_ref_code:
            eval_context = {
                "record": variant_id,
                "tmpl": self,
            }
            safe_eval(
                self.cpq_ref_code, eval_context, mode="exec", nocopy=True
            )  # nocopy allows to return 'ref'
            return eval_context.get("ref")

    def _cpq_get_create_variant_post_create_hook(self, variant_id):
        # We render the cpq_ref_tmpl after the creation so that we can pass in
        # the variant for simplicity on the template
        default_code = self._cpq_get_variant_ref(variant_id)
        if default_code:
            variant_id.default_code = default_code
        return variant_id

    def _cpq_get_combination_info(self):
        self.ensure_one()
        product_tmpl_id = self

        return {
            "product_tmpl_id": {
                "id": product_tmpl_id.id,
                "name": product_tmpl_id.name,
                "display_name": product_tmpl_id.display_name,
                "cpq_ref": product_tmpl_id.cpq_ref,
                "description_sale": product_tmpl_id.description_sale,
            },
            "ptal_ids": [
                i._cpq_get_combination_info()
                for i in product_tmpl_id.valid_product_template_attribute_line_ids
            ],
        }

    def _cpq_render_inline_template(self, template, extras=None):
        template_instructions = parse_inline_template(str(template))
        is_dynamic = len(template_instructions) > 1 or template_instructions[0][1]
        if is_dynamic:
            render_env = self._cpq_render_inline_template_context(extras)
            return render_inline_template(template_instructions, render_env)
        return template

    @api.model
    def _cpq_render_inline_template_context(self, extras=None):
        """
        Evaluation context used in all rendering engines.
        Contains
          * ``user``: current user browse record;
          * ``ctx```: current context;
          * various formatting tools;
        """
        render_context = {
            "format_date": lambda date, date_format=False, lang_code=False: format_date(
                self.env, date, date_format, lang_code
            ),
            "format_datetime": lambda dt,
            tz=False,
            dt_format=False,
            lang_code=False: format_datetime(self.env, dt, tz, dt_format, lang_code),
            "format_time": lambda time,
            tz=False,
            time_format=False,
            lang_code=False: format_time(self.env, time, tz, time_format, lang_code),
            "format_amount": lambda amount, currency, lang_code=False: format_amount(
                self.env, amount, currency, lang_code
            ),
            "format_duration": lambda value: format_duration(value),
            "user": self.env.user,
            "ctx": self._context,
            "is_html_empty": is_html_empty,
        }
        render_context.update(copy.copy(template_env_globals))

        if extras and isinstance(extras, dict):
            render_context.update(extras)

        return render_context

    def write(self, vals):
        res = super().write(vals)
        if "attribute_line_ids" in vals:
            self._cpq_archive_impossible_configurations()
        return res

    def _cpq_archive_impossible_configurations(self):
        archived = self.env["product.product"].with_context(active_test=False)

        for record in self.filtered(lambda p: p.cpq_ok):
            for variant in record.product_variant_ids:
                is_combination_possible = self._is_combination_possible_by_config(
                    combination=variant.product_template_attribute_value_ids,
                    ignore_no_variant=True,
                )
                if not is_combination_possible:
                    archived |= variant
                    variant.active = False
                    variant.message_post(
                        body=_(
                            "Auto-archived as no longer possible by configuration"
                            " (CPQ) through attribute change."
                        )
                    )

        return archived
