import datetime
import json

from babel.dates import format_date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.release import version
from odoo.tools.safe_eval import test_python_expr


class EdiBackend(models.Model):
    _name = "edi.backend"
    _description = "EDI Backend"
    _inherit = ["connector.backend"]

    name = fields.Char(required=True)
    partner_id = fields.Many2one("res.partner", index=True)
    colour = fields.Integer("Color Index", default=0)
    envelope_route_ids = fields.One2many(
        "edi.envelope.route", "backend_id", context={"active_test": False}
    )
    message_route_ids = fields.One2many(
        "edi.route", "backend_id", context={"active_test": False}, oldname="route_ids"
    )
    active = fields.Boolean(default=True)
    hint_duplicates = fields.Boolean(
        default=False,
        string="Allow Duplicate Messages?",
        hint="This is the responsibility of the message action to implement.",
    )
    hint_trust_partner = fields.Boolean(
        default=False,
        string="Trust Partner In Messages",
        hint="This is the responsibility of the message action to implement",
    )

    partner_ref = fields.Char(
        hint="""
Partner's reference
        """
    )
    our_ref = fields.Char(
        hint="""
Partner's reference for us
        """
    )
    mapping_ids = fields.One2many("edi.mapping", "backend_id")
    secret_ids = fields.One2many("edi.secret", "backend_id")
    common_code = fields.Text(
        "Common Python Code",
        help=(
            "A place for helpers and constants."
            " You can add here any functions or variables, that don't start with"
            " underscore and then reuse it in any other code for this backend."
        ),
    )

    def _get_default_envelope_sequence(self):
        return self.env.ref("connector_edi.sequence_envelope_out")

    envelope_sequence = fields.Many2one(
        "ir.sequence", required=True, default=_get_default_envelope_sequence
    )

    def _get_default_message_sequence(self):
        return self.env.ref("connector_edi.sequence_message_out")

    message_sequence = fields.Many2one(
        "ir.sequence", required=True, default=_get_default_message_sequence
    )

    def _get_default_subscribe_group_ids(self):
        return self.env.ref("connector.group_connector_manager")

    subscribe_group_ids = fields.Many2many(
        "res.groups", default=_get_default_subscribe_group_ids
    )
    subscribe_partner_ids = fields.Many2many("res.partner")

    def action_collect_envelopes(self):
        self.mapped("envelope_route_ids").filtered(
            lambda r: r.direction in ["in", "both"]
        ).collect_envelopes()

    def action_send_envelopes(self):
        self.mapped("envelope_route_ids").filtered(
            lambda r: r.direction in ["in", "both"]
        ).send_envelopes()

    def action_view_envelopes(self):
        action = self.env.ref("connector_edi.action_edi_envelope").read()[0]
        action["domain"] = [("backend_id", "in", self.ids)]
        return action

    def action_open_messages(self):
        """
        Open any pending messages
        """
        env = self.env["edi.envelope"].search(
            [
                ("state", "=", "pending"),
                ("direction", "=", "in"),
                ("backend_id", "in", self.ids),
            ]
        )
        if env:
            env.run()

        todo = self.env["edi.message"].search(
            [
                ("state", "=", "pending"),
                ("direction", "=", "in"),
                ("backend_id", "in", self.ids),
            ]
        )

        if todo:
            todo.action_read()

    def action_send_messages(self):
        """
        Generate/send messages
        """
        todo = self.mapped("message_route_ids").filtered(lambda r: r.direction == "out")
        if todo:
            todo.action_send_messages()

    def action_view_messages(self):
        action = self.env.ref("connector_edi.action_edi_message").read()[0]
        action["domain"] = [("backend_id", "in", self.ids)]
        return action

    def action_view_cron(self):
        cron_ids = self.mapped("envelope_route_ids.protocol_in_cron_id")
        cron_ids |= self.mapped("envelope_route_ids.protocol_out_cron_id")
        cron_ids |= self.mapped("message_route_ids.cron_id")

        action = self.env.ref("base.ir_cron_act").read()[0]
        action["domain"] = [("id", "in", cron_ids.ids)]
        return action

    def action_sync_cron(self):
        for record in self:
            record.envelope_route_ids.action_sync_cron()
            record.message_route_ids.action_sync_cron()

    def write(self, vals):
        res = super(EdiBackend, self).write(vals)

        trigger_fields = ["active", "name"]
        if any(i in trigger_fields for i in vals.keys()):
            self.action_sync_cron()

        return res

    envelope_count = fields.Integer(compute="_compute_envelope_count", store=False)

    def _compute_envelope_count(self):
        envelope_data = self.env["edi.envelope"].read_group(
            domain=[("backend_id", "in", self.ids)],
            fields=["backend_id"],
            groupby="backend_id",
        )

        mapped_data = {
            data["backend_id"][0]: data["backend_id_count"] for data in envelope_data
        }

        for record in self:
            record.envelope_count = mapped_data.get(record.id, 0)

    message_count = fields.Integer(compute="_compute_message_count", store=False)

    def _compute_message_count(self):
        message_data = self.env["edi.message"].read_group(
            domain=[("backend_id", "in", self.ids)],
            fields=["backend_id"],
            groupby="backend_id",
        )

        mapped_data = {
            data["backend_id"][0]: data["backend_id_count"] for data in message_data
        }

        for record in self:
            record.message_count = mapped_data.get(record.id, 0)

    kanban_dashboard_graph = fields.Text(compute="_compute_kanban_dashboard_graph")

    def _compute_kanban_dashboard_graph(self):
        for record in self:
            record.kanban_dashboard_graph = json.dumps(record._get_line_graph_data())

    def _get_line_graph_data(self):
        """
        Computes the data used to display the graph for on the kanban dashboard
        """

        def build_graph_data(date, amount):
            # display date in locale format
            name = format_date(date, "d LLLL Y", locale=locale)
            short_name = format_date(date, "d MMM", locale=locale)
            return {"x": short_name, "y": amount, "name": name}

        self.ensure_one()
        data = []
        date_today = datetime.datetime.today()
        date_start = date_today + datetime.timedelta(days=-7)
        locale = self._context.get("lang") or "en_US"

        # Using generate_series to ensure that we don't have any blank data
        # and a data point for each day in the last 7 days
        query = """
            SELECT
              s.date,
              COALESCE(d.amount, 0) AS amount
            FROM GENERATE_SERIES(%s, %s, '1d') AS s
            LEFT JOIN (
                SELECT
                    COUNT(*) AS amount,
                    DATE_TRUNC('day', create_date) AS date
                FROM edi_message
                WHERE
                    backend_id = %s
                    AND create_date > %s
                    AND create_date <= %s
                GROUP BY DATE_TRUNC('day', create_date)
            ) AS d ON d.date = s.date
            ORDER BY s.date ASC
        """
        self.env.cr.execute(
            query, (date_start, date_today, self.id, date_start, date_today)
        )
        for val in self.env.cr.dictfetchall():
            data.append(build_graph_data(val["date"], val["amount"]))

        # are we enterprise or not?
        color = "#875A7B" if "e" in version else "#7c7bad"

        return [
            {
                "values": data,
                "title": "Title",
                "key": _("Total Messages"),
                "area": True,
                "color": color,
            }
        ]

    def _mapping_to_external(self, record, fallback=None):
        self.ensure_one()
        result = self.mapping_ids.translate_to(record)
        if result:
            return result
        return fallback

    def _mapping_from_external(self, ref, fallback=None):
        self.ensure_one()
        result = self.mapping_ids.translate_from(ref)
        if result:
            return result
        return fallback

    def _subscribe_partners(self):
        self.ensure_one()
        partner_ids = self.subscribe_partner_ids

        if self.subscribe_group_ids:
            partner_ids |= (
                self.env["res.users"]
                .search([("groups_id", "in", self.subscribe_group_ids.ids)])
                .mapped("partner_id")
            )

        return partner_ids

    @api.constrains("common_code")
    def _check_python_code(self):
        for r in self.sudo().filtered("common_code"):
            msg = test_python_expr(expr=(r.common_code or "").strip(), mode="exec")
            if msg:
                raise ValidationError(msg)
