import datetime
import json
from collections import defaultdict

from babel.dates import format_date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.release import version
from odoo.tools.safe_eval import test_python_expr


class EdiBackend(models.Model):
    _name = "edi.backend"
    _description = "EDI Backend"
    _inherit = ["connector.backend", "edi.external_id.warning.mixin"]

    name = fields.Char(
        required=True,
    )

    active = fields.Boolean(
        default=True,
    )

    colour = fields.Integer(
        default=0,
    )

    partner_id = fields.Many2one(
        "res.partner",
        index=True,
    )

    envelope_message_routes_ok = fields.Boolean(
        default=True,
        string="Can Use Envelope & Message Routes",
    )

    hint_duplicates = fields.Boolean(
        "Allow Duplicate Messages?",
        help="This is the responsibility of the message action to implement.",
    )

    hint_trust_partner = fields.Boolean(
        "Trust Partner In Messages",
        help="This is the responsibility of the message action to implement.",
    )

    envelope_route_ids = fields.One2many(
        "edi.envelope.route",
        "backend_id",
        context={"active_test": False},
    )

    mapping_ids = fields.One2many(
        "edi.mapping",
        "backend_id",
    )

    secret_ids = fields.One2many(
        "edi.secret",
        "backend_id",
    )

    message_route_ids = fields.One2many(
        "edi.route",
        "backend_id",
        context={"active_test": False},
    )

    our_ref = fields.Char("Our Reference", help="The partner's reference for us.")

    partner_ref = fields.Char("Partner Reference", help="The partner's reference.")

    common_code = fields.Text(
        "Common Python Code",
    )

    def _get_default_envelope_sequence(self):
        return self.env.ref("connector_edi.sequence_envelope_out")

    envelope_sequence = fields.Many2one(
        "ir.sequence",
        default=_get_default_envelope_sequence,
        required=True,
    )

    def _get_default_message_sequence(self):
        return self.env.ref("connector_edi.sequence_message_out")

    message_sequence = fields.Many2one(
        "ir.sequence",
        default=_get_default_message_sequence,
        required=True,
    )

    def _get_default_subscribe_group_ids(self):
        return self.env.ref("connector.group_connector_manager")

    subscribe_group_ids = fields.Many2many(
        "res.groups",
        default=_get_default_subscribe_group_ids,
    )

    subscribe_partner_ids = fields.Many2many(
        "res.partner",
    )

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

        action.update(
            {
                "domain": [("backend_id", "in", self.ids)],
            }
        )

        return action

    def action_open_messages(self):
        self.env["edi.envelope"].search(
            [
                ("backend_id", "in", self.ids),
                ("direction", "=", "in"),
                ("state", "=", "pending"),
            ]
        ).run()

        self.env["edi.message"].search(
            [
                ("backend_id", "in", self.ids),
                ("direction", "=", "in"),
                ("state", "=", "pending"),
            ]
        ).action_read()

    def action_send_messages(self):
        self.mapped("message_route_ids").filtered(
            lambda r: r.direction == "out"
        ).action_send_messages()

    def action_view_messages(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_edi.action_edi_message"
        )

        action.update(
            {
                "domain": [("backend_id", "in", self.ids)],
            }
        )

        return action

    def action_view_cron(self):
        cron_ids = self.mapped("envelope_route_ids.protocol_in_cron_id")
        cron_ids |= self.mapped("envelope_route_ids.protocol_out_cron_id")
        cron_ids |= self.mapped("message_route_ids.cron_id")
        action = self.env["ir.actions.actions"]._for_xml_id("base.ir_cron_act")
        action["domain"] = [("id", "in", cron_ids.ids)]
        return action

    def action_sync_cron(self):
        for backend in self:
            backend.envelope_route_ids.action_sync_cron()
            backend.message_route_ids.action_sync_cron()

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
        res = super().write(vals)

        trigger_fields = ["active", "name"]

        if any(field in trigger_fields for field in vals.keys()):
            self.action_sync_cron()

        return res

    envelope_count = fields.Integer(
        compute="_compute_envelope_count",
    )

    envelope_done_count = fields.Integer(
        compute="_compute_message_count",
    )

    envelope_error_count = fields.Integer(
        compute="_compute_message_count",
    )

    envelope_pending_count = fields.Integer(
        compute="_compute_message_count",
    )

    envelope_with_legacy_body_count = fields.Integer(
        compute="_compute_envelope_with_legacy_body_count",
    )

    message_with_legacy_body_count = fields.Integer(
        compute="_compute_message_with_legacy_body_count",
    )

    def _compute_envelope_with_legacy_body_count(self):
        self.env.cr.execute(
            """
            SELECT
                backend_id, COUNT(*)
            FROM
                edi_envelope
            WHERE
                use_legacy_body = true
            AND
                backend_id in %(res_ids)s
            GROUP BY
                backend_id
        """,
            {"res_ids": tuple(self.ids)},
        )

        data = {i[0]: i[1] for i in self.env.cr.fetchall()}

        for backend in self:
            backend.envelope_with_legacy_body_count = data.get(backend.id, 0)

    def _compute_message_with_legacy_body_count(self):
        self.env.cr.execute(
            """
            SELECT
                backend_id, COUNT(*)
            FROM
                edi_message
            WHERE
                use_legacy_body = true
            AND
                backend_id in %(res_ids)s
            GROUP BY
                backend_id
        """,
            {"res_ids": tuple(self.ids)},
        )

        data = {i[0]: i[1] for i in self.env.cr.fetchall()}

        for backend in self:
            backend.message_with_legacy_body_count = data.get(backend.id, 0)

    def action_migrate_legacy_body_to_attachment(self):
        envelope_ids = self.env["edi.envelope"].search(
            [
                ("backend_id", "in", self.ids),
                ("use_legacy_body", "=", True),
            ]
        )

        message_ids = self.env["edi.message"].search(
            [
                ("backend_id", "in", self.ids),
                ("use_legacy_body", "=", True),
            ]
        )

        for envelope in envelope_ids:
            envelope.action_migrate_legacy_body_to_attachment()

        for message in message_ids:
            message.action_migrate_legacy_body_to_attachment()

    def _compute_envelope_count(self):
        self.env.cr.execute(
            """
            SELECT
                backend_id, COUNT(*), state
        FROM edi_envelope
        WHERE
            backend_id in %s
            and active is true
        GROUP BY backend_id, state
        """,
            [tuple(self.ids)],
        )

        mapped_data = defaultdict(lambda: defaultdict(lambda: 0))

        for i in self.env.cr.fetchall():
            backend, count, state = i
            mapped_data[backend]["__total"] += count
            mapped_data[backend][state] = count

        for record in self:
            record.envelope_count = mapped_data[record.id]["__total"]
            record.envelope_error_count = mapped_data[record.id]["error"]
            record.envelope_pending_count = mapped_data[record.id]["pending"]
            record.envelope_done_count = mapped_data[record.id]["done"]

    message_count = fields.Integer(
        compute="_compute_message_count",
    )

    message_done_count = fields.Integer(
        compute="_compute_message_count",
    )

    message_error_count = fields.Integer(
        compute="_compute_message_count",
    )

    message_pending_count = fields.Integer(
        compute="_compute_message_count",
    )

    def _compute_message_count(self):
        self.env.cr.execute(
            """
        SELECT
            backend_id, COUNT(*), state
        FROM edi_message
        WHERE
            backend_id in %s
            and active is true
        GROUP BY backend_id, state
        """,
            [tuple(self.ids)],
        )

        mapped_data = defaultdict(lambda: defaultdict(lambda: 0))

        for i in self.env.cr.fetchall():
            backend, count, state = i
            mapped_data[backend]["__total"] += count
            mapped_data[backend][state] = count

        for record in self:
            record.message_count = mapped_data[record.id]["__total"]
            record.message_error_count = mapped_data[record.id]["error"]
            record.message_pending_count = mapped_data[record.id]["pending"]
            record.message_done_count = mapped_data[record.id]["done"]

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
        return self.mapping_ids.translate_to(record) or fallback

    def _mapping_from_external(self, reference, fallback=None):
        self.ensure_one()
        return self.mapping_ids.translate_from(reference) or fallback

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
        for backend in self.sudo().filtered("common_code"):
            msg = test_python_expr(expr=backend.common_code.strip() or "", mode="exec")
            if msg:
                raise ValidationError(msg)
