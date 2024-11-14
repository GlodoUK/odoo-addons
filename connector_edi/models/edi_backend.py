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
    _inherit = ["connector.backend", "edi.external_id.warning.mixin"]

    name = fields.Char(required=True)
    partner_id = fields.Many2one("res.partner", index=True)
    colour = fields.Integer(default=0)
    envelope_message_routes_ok = fields.Boolean(
        default=True,
        string="Can use Envelope & Message Routes",
    )

    envelope_route_ids = fields.One2many(
        "edi.envelope.route", "backend_id", context={"active_test": False}
    )
    message_route_ids = fields.One2many(
        "edi.route", "backend_id", context={"active_test": False}
    )
    active = fields.Boolean(default=True)
    hint_duplicates = fields.Boolean(
        default=False,
        string="Allow Duplicate Messages?",
        help="This is the responsibility of the message action to implement.",
    )
    hint_trust_partner = fields.Boolean(
        default=False,
        string="Trust Partner In Messages",
        help="This is the responsibility of the message action to implement",
    )

    partner_ref = fields.Char(help="Partner's reference")
    our_ref = fields.Char(help="Partner's reference for us")
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
        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_edi.action_edi_envelope"
        )
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
        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_edi.action_edi_message"
        )
        action["domain"] = [("backend_id", "in", self.ids)]
        return action

    def action_view_cron(self):
        cron_ids = self.mapped("envelope_route_ids.protocol_in_cron_id")
        cron_ids |= self.mapped("envelope_route_ids.protocol_out_cron_id")
        cron_ids |= self.mapped("message_route_ids.cron_id")
        action = self.env["ir.actions.actions"]._for_xml_id("base.ir_cron_act")
        action["domain"] = [("id", "in", cron_ids.ids)]
        return action

    def action_sync_cron(self):
        for record in self:
            record.envelope_route_ids.action_sync_cron()
            record.message_route_ids.action_sync_cron()

    def action_upload_file(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "edi.upload.file",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {"default_backend_id": self.id},
        }

    def write(self, vals):
        res = super(EdiBackend, self).write(vals)

        trigger_fields = ["active", "name"]
        if any(i in trigger_fields for i in vals.keys()):
            self.action_sync_cron()

        return res

    envelope_count = fields.Integer(
        compute="_compute_envelope_count",
        store=False,
    )
    envelope_pending_count = fields.Integer(
        compute="_compute_message_count", store=False
    )
    envelope_error_count = fields.Integer(compute="_compute_message_count", store=False)
    envelope_done_count = fields.Integer(compute="_compute_message_count", store=False)

    envelope_with_legacy_body_count = fields.Integer(
        compute="_compute_envelope_with_legacy_body_count"
    )
    message_with_legacy_body_count = fields.Integer(
        compute="_compute_message_with_legacy_body_count"
    )

    def _compute_envelope_with_legacy_body_count(self):
        self.env.cr.execute(
            """
        SELECT
            backend_id, COUNT(*)
        FROM edi_envelope
        WHERE
            use_legacy_body = true
            and backend_id in %s
        GROUP BY backend_id
        """,
            [tuple(self.ids)],
        )

        data = {i[0]: i[1] for i in self.env.cr.fetchall()}

        for record in self:
            record.envelope_with_legacy_body_count = data.get(record.id, 0)

    def _compute_message_with_legacy_body_count(self):
        self.env.cr.execute(
            """
        SELECT
            backend_id, COUNT(*)
        FROM edi_message
        WHERE
            use_legacy_body = true
            and backend_id in %s
        GROUP BY backend_id
        """,
            [tuple(self.ids)],
        )

        data = {i[0]: i[1] for i in self.env.cr.fetchall()}

        for record in self:
            record.message_with_legacy_body_count = data.get(record.id, 0)

    def action_migrate_legacy_body_to_attachment(self):
        edi_envelope_ids = self.env["edi.envelope"].search(
            [
                ("backend_id", "in", self.ids),
                ("use_legacy_body", "=", True),
            ]
        )

        for edi_envelope_id in edi_envelope_ids:
            edi_envelope_id.action_migrate_legacy_body_to_attachment()

        edi_message_ids = self.env["edi.message"].search(
            [
                ("backend_id", "in", self.ids),
                ("use_legacy_body", "=", True),
            ]
        )

        for edi_message_id in edi_message_ids:
            edi_message_id.action_migrate_legacy_body_to_attachment()

    def _compute_envelope_count(self):
        envelope_data = self.env["edi.envelope"].read_group(
            domain=[("backend_id", "in", self.ids)],
            fields=["backend_id", "state"],
            groupby=["backend_id", "state"],
            lazy=False,
        )

        mapped_data = {}

        for i in envelope_data:
            backend = i["backend_id"][0]
            state = i["state"]
            if backend not in mapped_data:
                mapped_data[backend] = {
                    "__total": 0,
                }

            mapped_data[backend]["__total"] += i["__count"]
            mapped_data[backend][state] = i["__count"]

        for record in self:
            record.envelope_count = mapped_data.get(record.id, {}).get("__total", 0.0)
            record.envelope_error_count = mapped_data.get(record.id, {}).get(
                "error", 0.0
            )
            record.envelope_pending_count = mapped_data.get(record.id, {}).get(
                "pending", 0.0
            )
            record.envelope_done_count = mapped_data.get(record.id, {}).get("done", 0.0)

    message_count = fields.Integer(compute="_compute_message_count", store=False)
    message_pending_count = fields.Integer(
        compute="_compute_message_count", store=False
    )
    message_error_count = fields.Integer(compute="_compute_message_count", store=False)
    message_done_count = fields.Integer(compute="_compute_message_count", store=False)

    def _compute_message_count(self):
        message_data = self.env["edi.message"].read_group(
            domain=[("backend_id", "in", self.ids)],
            fields=["backend_id", "state"],
            groupby=["backend_id", "state"],
            lazy=False,
        )

        mapped_data = {}

        for i in message_data:
            backend = i["backend_id"][0]
            state = i["state"]
            if backend not in mapped_data:
                mapped_data[backend] = {
                    "__total": 0,
                }

            mapped_data[backend]["__total"] += i["__count"]
            mapped_data[backend][state] = i["__count"]

        for record in self:
            record.message_count = mapped_data.get(record.id, {}).get("__total", 0.0)
            record.message_error_count = mapped_data.get(record.id, {}).get(
                "error", 0.0
            )
            record.message_pending_count = mapped_data.get(record.id, {}).get(
                "pending", 0.0
            )
            record.message_done_count = mapped_data.get(record.id, {}).get("done", 0.0)

    show_kanban_dashboard_graph = fields.Boolean(
        default=True,
        help="When displaying a large number of graphs the Odoo web client can"
        " slow down. Toggle this to disable the graph on a per-backend basis.",
    )
    kanban_dashboard_graph = fields.Text(compute="_compute_kanban_dashboard_graph")

    def _compute_kanban_dashboard_graph(self):
        for record in self:
            if record.show_kanban_dashboard_graph:
                record.kanban_dashboard_graph = json.dumps(
                    record._get_line_graph_data()
                )
            else:
                record.kanban_dashboard_graph = False

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
