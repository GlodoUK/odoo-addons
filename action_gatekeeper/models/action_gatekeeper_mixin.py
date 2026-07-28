from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ActionGatekeeperMixin(models.AbstractModel):
    _name = "gatekeeper.mixin"
    _description = "Action Gatekeeper Mixin"

    gatekeeper_hold = fields.Boolean(
        copy=False,
    )

    gatekeeper_rule_lines = fields.Many2many(
        comodel_name="gatekeeper.line",
        copy=False,
        readonly=True,
    )

    def _compute_gatekeeper_rule_lines_waiting(self):
        for record in self:
            record.gatekeeper_rule_lines_waiting = any(
                not line.is_released for line in record.gatekeeper_rule_lines
            )

    def _get_gatekeeper_rules(self, event=None):
        self.ensure_one()
        domain = [("target_model", "=", self._name)]
        if event:
            domain.append(("trigger.action", "=", event))
        rules = self.env["gatekeeper.rule"].search(
            domain,
            order="sequence",
        )
        for rule in rules:
            if rule.target_domain:
                domain = safe_eval(rule.target_domain)
                if not self.filtered_domain(domain):
                    rules -= rule
        return rules

    def _sync_gatekeeper_lines(self):
        if self.env.context.get("skip_gatekeeper_sync"):
            return

        line_model = self.env["gatekeeper.line"].sudo()

        for record in self:
            lines = self.env["gatekeeper.line"]
            existing = record.gatekeeper_rule_lines

            rules = record._get_gatekeeper_rules()

            existing_to_remove = existing.filtered(
                lambda line, rules=rules: line.rule_id not in rules
            )
            lines -= existing_to_remove
            existing -= existing_to_remove

            lines |= existing

            for rule in rules:
                if rule not in existing.mapped("rule_id"):
                    line = line_model.create(
                        {
                            "rule_id": rule.id,
                            "action": rule.action,
                            "res_id": record.id,
                        }
                    )
                    lines |= line
            record.with_context(
                skip_gatekeeper_sync=True, skip_gatekeeper_check=True
            ).write({"gatekeeper_rule_lines": [(6, 0, lines.ids)]})

    def _check_gatekeeper_rules(self, event):
        self.ensure_one()
        rules = self._get_gatekeeper_rules(event)
        if rules:
            for rule in rules.filtered(lambda r: r.trigger.action == event):
                if rule._check_rule(self):
                    if rule.action == "hold":
                        self._action_gatekeeper_hold(rule)
                    else:
                        record_name = getattr(self, "name", "")
                        block_message = rule.block_message or self.env._(
                            "Blocked by Gatekeeper Rule!"
                        )
                        raise ValidationError(
                            self.env._(
                                "%(block_message)s"
                                "\nModel: %(model_name)s "
                                "ID: %(record_id)s%(record_name)s"
                                "\nRule: %(rule_name)s",
                                block_message=block_message,
                                model_name=self._name,
                                record_id=self.id,
                                record_name="\n" + record_name if record_name else "",
                                rule_name=rule.name,
                            )
                        )

    def create(self, vals):
        res = super().create(vals)
        res._sync_gatekeeper_lines()
        for record in res:
            record._check_gatekeeper_rules("create")
        return res

    def write(self, vals):
        res = super().write(vals)
        self._sync_gatekeeper_lines()
        if not self.env.context.get("skip_gatekeeper_check"):
            for record in self:
                record._check_gatekeeper_rules("write")
        return res

    def _action_gatekeeper_hold(self, rule_id):
        self.ensure_one()
        self.gatekeeper_hold = True

    def _release_gatekeeper_hold(self):
        self.ensure_one()
        self.gatekeeper_hold = False

    def _reset_gatekeeper_rules(self):
        self.ensure_one()
        self.gatekeeper_rule_lines = [(5, 0, 0)]
        self.gatekeeper_hold = False
