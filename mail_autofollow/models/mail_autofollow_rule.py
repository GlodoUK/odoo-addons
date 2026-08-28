import logging
from collections import defaultdict

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)

APPLY_BATCH_SIZE = 1000


class MailAutofollowRule(models.Model):
    _name = "mail_autofollow.rule"
    _description = "Automatic Follower Rule"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(
        default=True,
        help="Set inactive to keep the rule for reference without applying it.",
    )
    sequence = fields.Integer(default=10)
    model_id = fields.Many2one(
        "ir.model",
        required=True,
        ondelete="cascade",
        domain=[("is_mail_thread", "=", True), ("transient", "=", False)],
        help="Model the rule applies to. Only models with a chatter can have "
        "followers.",
    )
    model_name = fields.Char(
        related="model_id.model",
        string="Model Name",
        store=True,
        index=True,
        readonly=True,
    )
    filter_domain = fields.Char(
        string="Apply on",
        default="[]",
        help="Records matching this domain get the followers below. An empty "
        "domain matches every record of the model.",
    )
    partner_ids = fields.Many2many(
        "res.partner",
        string="Followers",
        help="Contacts subscribed to the records matched by this rule. Pick a "
        "user's contact to subscribe that user.",
    )
    follower_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Follower Fields",
        domain="[('model_id', '=', model_id), "
        "('relation', 'in', ('res.partner', 'res.users')), "
        "('ttype', 'in', ('many2one', 'many2many', 'one2many'))]",
        help="Fields of the record whose contacts follow it: its salesperson, "
        "its customer, a manager. A field pointing at users subscribes those "
        "users' contacts. Resolved per record, on top of the fixed followers "
        "above.",
    )
    subtype_ids = fields.Many2many(
        "mail.message.subtype",
        string="Subscribe To",
        domain="['|', ('res_model', '=', False), ('res_model', '=', model_name)]",
        help="Subscription subtypes of the new followers. Leave empty to use "
        "the model's default subscription, which is what the chatter's "
        "'Add Followers' does.",
    )
    trigger = fields.Selection(
        selection=[
            ("on_create", "On Creation"),
            ("on_create_or_write", "On Creation & Update"),
        ],
        required=True,
        default="on_create",
        help="'On Creation' subscribes the followers as the record is created, "
        "before the creation message is posted. 'On Creation & Update' also "
        "re-checks the domain on every write, so records that start matching "
        "later are covered too (a follower removed by hand comes back on the "
        "next write).",
    )
    company_id = fields.Many2one(
        "res.company",
        help="Leave empty to apply the rule in every company.",
    )

    @api.constrains("model_id")
    def _check_model_id(self):
        for rule in self:
            if not rule.model_id.is_mail_thread:
                raise ValidationError(
                    self.env._(
                        "%(model)s has no chatter, it cannot have followers.",
                        model=rule.model_id.display_name,
                    )
                )

    @api.constrains("filter_domain", "model_id")
    def _check_filter_domain(self):
        for rule in self:
            try:
                rule._get_domain().validate(self.env[rule.model_name])
            except ValidationError:
                raise
            except Exception as exc:
                raise ValidationError(
                    self.env._(
                        "Invalid domain on rule %(rule)s: %(error)s",
                        rule=rule.display_name,
                        error=exc,
                    )
                ) from exc

    @api.constrains("subtype_ids", "model_id")
    def _check_subtype_ids(self):
        for rule in self:
            invalid = rule.subtype_ids.filtered(
                lambda subtype, rule=rule: (
                    subtype.res_model not in (False, rule.model_name)
                )
            )
            if invalid:
                raise ValidationError(
                    self.env._(
                        "Subtypes %(subtypes)s do not apply to %(model)s.",
                        subtypes=", ".join(invalid.mapped("display_name")),
                        model=rule.model_id.display_name,
                    )
                )

    @api.constrains("follower_field_ids", "model_id")
    def _check_follower_field_ids(self):
        for rule in self:
            invalid = rule.follower_field_ids.filtered(
                lambda field, rule=rule: (
                    field.model != rule.model_name
                    or field.relation not in ("res.partner", "res.users")
                )
            )
            if invalid:
                raise ValidationError(
                    self.env._(
                        "Fields %(fields)s are not contact fields of %(model)s.",
                        fields=", ".join(invalid.mapped("display_name")),
                        model=rule.model_id.display_name,
                    )
                )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        self.filter_domain = "[]"
        self.subtype_ids = False
        self.follower_field_ids = False

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        self.env.registry.clear_cache()
        return rules

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res

    @api.model
    @tools.ormcache("model_name")
    def _rule_ids_for_model(self, model_name):
        return tuple(
            self.sudo()
            .with_context(active_test=True)
            .search([("model_name", "=", model_name)])
            .ids
        )

    @api.model
    def _rules_for_model(self, model_name, triggers=None):
        rules = self.sudo().browse(self._rule_ids_for_model(model_name))
        if triggers is not None:
            rules = rules.filtered(lambda rule: rule.trigger in triggers)
        return rules

    def _get_eval_context(self):
        return {
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "uid": self.env.uid,
            "user": self.env.user,
        }

    def _get_domain(self):
        self.ensure_one()
        if not self.filter_domain:
            return Domain.TRUE
        return Domain(safe_eval.safe_eval(self.filter_domain, self._get_eval_context()))

    def _filter_company(self, records):
        self.ensure_one()
        company_field = records._fields.get("company_id")
        if (
            not self.company_id
            or not company_field
            or company_field.comodel_name != "res.company"
        ):
            return records
        return records.filtered(
            lambda record: not record.company_id or record.company_id == self.company_id
        )

    def _match(self, records):
        self.ensure_one()
        records = self._filter_company(records)
        if not records or not self.filter_domain:
            return records
        return records.sudo().filtered_domain(self._get_domain()).with_env(records.env)

    def _resolve_field_followers(self, record):
        self.ensure_one()
        partners = self.env["res.partner"].browse()
        for field in self.follower_field_ids:
            if field.name not in record._fields:
                # the rule outlived the field (module uninstalled, studio field
                # dropped): a stale row must not break every create
                continue
            values = record[field.name]
            if not values:
                continue
            if field.relation == "res.users":
                values = values.filtered("active").partner_id
            partners |= values
        return partners.filtered("active")

    def _follower_groups(self, records):
        self.ensure_one()
        groups = defaultdict(list)
        if not self.follower_field_ids:
            if self.partner_ids:
                groups[frozenset(self.partner_ids.ids)] = records.ids
            return groups
        # sudo: a follower field may be one the acting user cannot read
        for record in records.sudo():
            partners = self.partner_ids | self._resolve_field_followers(record)
            if partners:
                groups[frozenset(partners.ids)].append(record.id)
        return groups

    def _subscribe(self, records):
        self.ensure_one()
        if not records:
            return
        subtype_ids = self.subtype_ids.ids
        Followers = self.env["mail.followers"]
        for partners, res_ids in self._follower_groups(records).items():
            partner_ids = list(partners)
            # no explicit subtype: let mail.followers compute the model
            # defaults, which also keeps internal subtypes away from portal
            # contacts
            subtypes = (
                {pid: subtype_ids for pid in partner_ids} if subtype_ids else None
            )
            for index in range(0, len(res_ids), APPLY_BATCH_SIZE):
                Followers._insert_followers(
                    records._name,
                    res_ids[index : index + APPLY_BATCH_SIZE],
                    partner_ids,
                    subtypes=subtypes,
                    check_existing=True,
                    existing_policy="skip",
                )

    def _apply(self, records):
        self.ensure_one()
        self._subscribe(self._match(records))

    @api.model
    def _apply_all(self, records, triggers):
        if not records or self.env.context.get("mail_autofollow_skip"):
            return
        for rule in self._rules_for_model(records._name, triggers=triggers):
            rule._apply(records)

    def action_apply_to_existing(self):
        count = 0
        for rule in self:
            if not rule.partner_ids and not rule.follower_field_ids:
                raise UserError(
                    self.env._(
                        "Rule %s has no follower to subscribe.", rule.display_name
                    )
                )
            # the domain is a search here, only the company scope is left
            # to filter in Python
            records = rule._filter_company(
                self.env[rule.model_name].sudo().search(rule._get_domain())
            )
            rule._subscribe(records)
            _logger.info(
                "mail_autofollow.rule %s applied to %s existing %s records",
                rule.id,
                len(records),
                rule.model_name,
            )
            count += len(records)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._("%s existing records updated.", count),
            },
        }
