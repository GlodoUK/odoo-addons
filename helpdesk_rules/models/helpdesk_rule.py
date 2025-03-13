from odoo import api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval, test_python_expr

from odoo.addons.helpdesk.models.helpdesk_ticket import TICKET_PRIORITY


class HelpdeskRule(models.Model):
    _name = "helpdesk.rule"
    _description = "Helpdesk Rule"
    _order = "sequence ASC"

    name = fields.Char(required=True)
    sequence = fields.Integer(required=True, default=20)
    team_id = fields.Many2one("helpdesk.team", required=True)
    active = fields.Boolean(default=True)
    trigger = fields.Selection(
        [
            ("on_create", "New Ticket"),
            ("on_write", "Ticket Update"),
            ("on_reply", "Incoming Reply"),
        ],
        required=True,
    )
    domain = fields.Char(default="[]", required=True)
    action = fields.Selection(
        [
            ("code", "Execute Python Code"),
            ("archive", "Archive Ticket"),
            ("set_stage", "Move to Stage"),
            ("change_tags", "Change Tags"),
            ("set_priority", "Set Priority"),
        ],
        required=True,
    )
    code = fields.Text()
    stage_id = fields.Many2one("helpdesk.stage", required=False)
    tag_ids = fields.One2many("helpdesk.rule.tag.action", "rule_id")
    priority = fields.Selection(TICKET_PRIORITY, required=False)
    stop = fields.Boolean(string="Stop after processing", default=True)
    debug = fields.Boolean(
        default=True, help="Post message in ticket chatter when applied"
    )

    def apply(self, ticket_id):
        applied_rule_ids = self.env["helpdesk.rule"]

        for record in self:
            domain = safe_eval(
                record.domain,
                {"user": self.env.user.with_user(self.env.user), "ticket": ticket_id},
            )

            if not ticket_id.filtered_domain(domain):
                continue

            record._execute(ticket_id)

            if record.debug:
                applied_rule_ids |= record

            if record.stop:
                break

        if applied_rule_ids:
            msg = "\n".join(
                [
                    (
                        '<li><a href=# data-oe-model="helpdesk.rule"'
                        " data-oe-id=%d>%s</a></li>"
                    )
                    % (record.id, record.name)
                    for record in applied_rule_ids
                ]
            )
            msg = "<p>Applied Helpdesk Rules:</p> <ul>%s</ul>" % msg

            ticket_id.sudo().message_post(body=msg)

    def _execute(self, ticket_id):
        self.ensure_one()

        method_name = f"_execute_{self.action}"

        return getattr(self, method_name)(ticket_id)

    def _execute_code(self, ticket_id):
        eval_context = self._get_eval_context(ticket_id)
        safe_eval(
            self.code.strip(), eval_context, mode="exec", nocopy=True
        )  # nocopy allows to return 'action'
        if "action" in eval_context:
            return eval_context["action"]
        return False

    def _get_eval_context(self, ticket_id):
        eval_context = {
            # orm
            "env": self.env,
            "Warning": exceptions.Warning,
            # record
            "record": ticket_id,
            "records": ticket_id,
        }
        return eval_context

    @api.constrains("code")
    def _check_python_code(self):
        for record in self.sudo().filtered("code"):
            msg = test_python_expr(expr=record.code.strip(), mode="exec")
            if msg:
                raise exceptions.ValidationError(msg)

    def _execute_archive(self, ticket_id):
        ticket_id.active = False

    def _execute_set_stage(self, ticket_id):
        ticket_id.stage_id = self.stage_id

    def _execute_change_tags(self, ticket_id):
        for tag_action in self.tag_ids:
            if tag_action.action == "add" and tag_action.tag_id:
                ticket_id.tag_ids |= tag_action.tag_id
            elif tag_action.action == "remove" and tag_action.tag_id:
                ticket_id.tag_ids -= tag_action.tag_id
            elif tag_action.action == "clear":
                ticket_id.tag_ids = False

    def _execute_set_priority(self, ticket_id):
        ticket_id.priority = self.priority
