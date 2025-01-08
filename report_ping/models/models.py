import ast
import base64
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ReportPing(models.Model):
    _name = "report.ping"
    _inherit = ["mail.thread"]

    name = fields.Char()
    template_id = fields.Many2one(
        "mail.template", domain=[("model_id.model", "=", "res.partner")]
    )
    active = fields.Boolean(default=True)

    report_ids = fields.One2many("report.ping.attach", "ping_id")

    cron_active = fields.Boolean()
    cron_interval = fields.Integer()

    cron_interval_type = fields.Selection(
        [
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
        default="days",
    )

    cron_id = fields.Many2one("ir.cron")

    def _cron_vals(self):
        self.ensure_one()

        vals = {
            "name": "Report Ping: %s" % (self.name),
            "active": self.cron_active,
            "numbercall": -1,
            "interval_number": self.cron_interval,
            "interval_type": self.cron_interval_type,
            "model_id": self.env["ir.model"].search([("model", "=", self._name)]).id,
            "code": """
record = model.browse(%d)
if record.active:
    record.send_ping()
            """
            % (self.id),
        }

        return vals

    def _cron_sync(self):
        self.ensure_one()
        vals = self._cron_vals()

        if not self.cron_id:
            self.cron_id = self.env["ir.cron"].create(vals)
        else:
            self.cron_id.write(vals)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res:
            res._cron_sync()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)

        for record in self:
            record._cron_sync()

        return res

    @api.multi
    def unlink(self):
        cron_ids = self.mapped("cron_id")
        if cron_ids:
            cron_ids.unlink()

        return super().unlink()

    @api.multi
    def send_ping(self):
        for record in self:
            record._send_ping()

    def _send_ping(self):
        self.ensure_one()

        email_values = {"attachments": []}

        for report_id in self.report_ids:
            data = report_id.render()
            if data:
                email_values["attachments"].append(data)

        for res_id in self.message_partner_ids:
            self.template_id.send_mail(
                res_id.id,
                email_values=email_values,
                force_send=True,
                notif_layout=False,
            )

            self.message_post(
                body=_("We've pinged <a href=# data-oe-model=%s data-oe-id=%d>%s</a>")
                % (res_id._name, res_id.id, res_id.display_name)
            )

    def action_add_follower(self):
        self.ensure_one()
        ctx = self.env.context.copy()

        ctx.update(
            {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_send_mail": False,
            }
        )

        view_id = self.env.ref("mail.mail_wizard_invite_form")

        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.wizard.invite",
            "views": [(view_id.id, "form")],
            "view_id": view_id.id,
            "target": "new",
            "context": ctx,
        }


class ReportPingAttachment(models.Model):
    _name = "report.ping.attach"

    ping_id = fields.Many2one("report.ping")

    report_id = fields.Many2one("ir.actions.report")

    model_name = fields.Char(related="report_id.model")

    model_domain = fields.Char(default="[]")

    def render(self):
        self.ensure_one()

        if self.model_name not in self.env:
            raise UserError(_("Model %s not found in environment!") % (self.model_name))

        domain = ast.literal_eval(self.model_domain)

        res_ids = self.env[self.model_name].search(domain)

        if not res_ids:
            return

        data = self.report_id.render(res_ids.ids)
        if not data:
            return

        extension = data[1] if not data[1] == "text" else "txt"

        if self.report_id.print_report_name and not len(res_ids) > 1:
            report_name = safe_eval(
                self.report_id.print_report_name, {"object": res_ids, "time": time}
            )
            filename = "{}.{}".format(report_name, extension)

        return (filename, base64.b64encode(data[0]))
