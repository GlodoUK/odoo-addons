from odoo import api, fields, models
from odoo.tools import SQL

STATUSES = [
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("error", "Error"),
    ("done", "Done"),
    ("cancelled", "Cancelled"),
]

# What a source's SELECT returns. The pane adds id, res_model and record.
COLUMNS = {
    "res_id": "integer",
    "backend": "varchar",
    "company_id": "integer",
    "state": "varchar",
    "status": "varchar",
    "error": "text",
    "date": "timestamp",
}


class AutopilotActivity(models.Model):
    """Every connector's records and their states, in one read-only list.

    A UNION ALL built from the registry on each read (``_table_query``, as
    ``sale.report``), not a database view: a view would block a source's
    column changes and vanish with its table. A model is a source by
    returning a SELECT of ``COLUMNS`` from ``_autopilot_activity_query()``,
    its own state mapped onto ``STATUSES``. :meth:`_source_select` writes the
    usual one::

        @api.model
        def _autopilot_activity_query(self):
            return self.env["autopilot.activity"]._source_select(
                self,
                backend="backend_id",
                company="company_id",
                state="state",
                status={"pending": "pending", "done": "done", "error": "error"},
                error="error_message",
                date="import_date",
            )

    Optional hooks on a source: ``_autopilot_activity_state_labels()``
    (``{state: label}``, default its ``state`` selection),
    ``_autopilot_activity_retry()`` (offered on error or cancelled) and
    ``_autopilot_activity_cancel()`` (offered on draft, pending or error).

    ``id`` is the ``ir.model`` id in the high 32 bits and the record id in the
    low ones, so it stays stable across reads.
    """

    _name = "autopilot.activity"
    _description = "Integration Activity"
    _auto = False
    _order = "date desc, id desc"
    _rec_name = "name"

    res_model = fields.Selection(
        selection="_selection_res_model", string="Type", readonly=True
    )
    res_id = fields.Integer(string="Record ID", readonly=True)
    record = fields.Reference(selection="_selection_res_model", readonly=True)
    backend = fields.Reference(selection="_selection_backend", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    state = fields.Char(readonly=True)
    status = fields.Selection(STATUSES, readonly=True)
    error = fields.Text(readonly=True)
    date = fields.Datetime(readonly=True)

    name = fields.Char(compute="_compute_name")
    state_label = fields.Char(string="State", compute="_compute_state_label")
    can_retry = fields.Boolean(compute="_compute_actions")
    can_cancel = fields.Boolean(compute="_compute_actions")

    # ------------------------------------------------------------------
    # Sources
    # ------------------------------------------------------------------
    @api.model
    def _sources(self):
        """Source model names, in ``ir.model`` order."""
        names = [
            name
            for name, model in self.env.registry.items()
            if hasattr(model, "_autopilot_activity_query")
            and not model._abstract
            and not model._transient
            and not model._table_query
        ]
        return sorted(names, key=self.env["ir.model"]._get_id)

    @api.model
    def _selection_res_model(self):
        return [(name, self.env[name]._description) for name in self._sources()]

    @api.model
    def _selection_backend(self):
        # A backend can be any connector's model.
        return [
            (model.model, model.name)
            for model in self.env["ir.model"].sudo().search([])
        ]

    @property
    def _table_query(self):
        parts = [self._wrap(name) for name in self._sources()]
        if not parts:
            return SQL(
                "SELECT NULL::bigint AS id, NULL::varchar AS res_model, "
                "NULL::varchar AS record, %s WHERE FALSE",
                SQL(", ").join(
                    SQL(f"NULL::{kind} AS %s", SQL.identifier(column))
                    for column, kind in COLUMNS.items()
                ),
            )
        return SQL(" UNION ALL ").join(parts)

    def _wrap(self, name):
        """Casts each column, so parts line up whatever their own types."""
        columns = SQL(", ").join(
            SQL(
                f"part.%s::{kind} AS %s",
                SQL.identifier(column),
                SQL.identifier(column),
            )
            for column, kind in COLUMNS.items()
        )
        return SQL(
            """
            SELECT (%(model_id)s::bigint << 32) | part.res_id AS id,
                   %(name)s::varchar AS res_model,
                   %(name)s || ',' || part.res_id AS record,
                   %(columns)s
              FROM (%(part)s) AS part
            """,
            model_id=self.env["ir.model"]._get_id(name),
            name=name,
            columns=columns,
            part=self.env[name]._autopilot_activity_query(),
        )

    @api.model
    def _source_select(
        self,
        source,
        state,
        status,
        backend=None,
        company=None,
        error=None,
        date="create_date",
    ):
        """One row per record of ``source``. Each argument is a field name or
        an ``SQL`` expression over alias ``src``. ``backend`` is a Many2one.
        ``status`` maps the source's states onto ``STATUSES``; unlisted states
        get none."""

        def column(value):
            if value is None:
                return SQL("NULL")
            if isinstance(value, SQL):
                return value
            return SQL.identifier("src", value)

        if isinstance(backend, str):
            comodel = source._fields[backend].comodel_name
            backend_sql = SQL(
                "%s || ',' || %s", comodel, SQL.identifier("src", backend)
            )
        else:
            backend_sql = column(backend)
        state_sql = column(state)
        status_sql = SQL(
            "CASE (%s) %s END",
            state_sql,
            SQL(" ").join(
                SQL("WHEN %s THEN %s", key, value) for key, value in status.items()
            ),
        )
        return SQL(
            """
            SELECT src.id AS res_id,
                   %s AS backend,
                   %s AS company_id,
                   %s AS state,
                   %s AS status,
                   %s AS error,
                   %s AS date
              FROM %s AS src
            """,
            backend_sql,
            column(company),
            state_sql,
            status_sql,
            column(error),
            column(date),
            SQL.identifier(source._table),
        )

    def _source_record(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id)

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("record")
    def _compute_name(self):
        for activity in self:
            # Admins only here. The record's own rules apply when it's opened.
            record = activity.record
            activity.name = record.sudo().display_name if record else ""

    @api.depends("res_model", "state")
    def _compute_state_label(self):
        labels = {}
        for activity in self:
            name = activity.res_model
            if name not in labels:
                labels[name] = self._state_labels(self.env[name]) if name else {}
            activity.state_label = labels[name].get(activity.state, activity.state)

    @api.model
    def _state_labels(self, source):
        method = getattr(source, "_autopilot_activity_state_labels", None)
        if method:
            return method()
        field = source._fields.get("state")
        if field and field.type == "selection":
            return dict(field._description_selection(self.env))
        return {}

    @api.depends("res_model", "status")
    def _compute_actions(self):
        for activity in self:
            source = self.env[activity.res_model] if activity.res_model else None
            activity.can_retry = hasattr(
                source, "_autopilot_activity_retry"
            ) and activity.status in ("error", "cancelled")
            activity.can_cancel = hasattr(
                source, "_autopilot_activity_cancel"
            ) and activity.status in ("draft", "pending", "error")

    # ------------------------------------------------------------------
    # Actions: on the record itself
    # ------------------------------------------------------------------
    def action_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
            "target": "current",
        }

    def action_retry(self):
        return self._call_source("_autopilot_activity_retry", "can_retry")

    def action_cancel(self):
        return self._call_source("_autopilot_activity_cancel", "can_cancel")

    def _call_source(self, method, allowed):
        result = None
        for activity in self.filtered(allowed):
            result = getattr(activity._source_record(), method)()
        return result if len(self) == 1 and isinstance(result, dict) else True
