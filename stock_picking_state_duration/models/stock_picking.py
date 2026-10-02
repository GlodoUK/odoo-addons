from odoo import api, fields, models
from odoo.tools import SQL

UNTIMED_STATES = ("draft", "done", "cancel")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    state_date = fields.Datetime(
        string="State Since",
        compute="_compute_state_date",
        store=True,
        readonly=True,
        copy=False,
        help="When the transfer entered its current state.",
    )
    # The state state_date was stamped for. state is recomputed whenever its
    # moves change, even if the value ends up the same, so compare against
    # this rather than restamping on every recompute.
    state_date_state = fields.Char(
        compute="_compute_state_date",
        store=True,
        readonly=True,
        copy=False,
    )
    state_duration = fields.Integer(
        string="Time in State",
        compute="_compute_state_duration",
        help="Seconds the transfer has spent in its current state. Empty for "
        "draft, done and cancelled transfers.",
    )

    @api.depends("state")
    def _compute_state_date(self):
        now = fields.Datetime.now()
        for picking in self:
            if picking.state != picking.state_date_state:
                picking.state_date = now
                picking.state_date_state = picking.state

    @api.depends("state", "state_date")
    def _compute_state_duration(self):
        now = fields.Datetime.now()
        for picking in self:
            if picking.state in UNTIMED_STATES or not picking.state_date:
                picking.state_duration = False
            else:
                picking.state_duration = int((now - picking.state_date).total_seconds())

    def _order_field_to_sql(self, alias, field_name, direction, nulls, query):
        if field_name == "state_duration":
            # Longest in state == earliest state_date, so flip the direction.
            sql_field = SQL(
                "CASE WHEN %s IN %s THEN NULL ELSE %s END",
                self._field_to_sql(alias, "state", query),
                UNTIMED_STATES,
                self._field_to_sql(alias, "state_date", query),
            )
            direction = SQL("ASC") if direction.code == "DESC" else SQL("DESC")
            return SQL("%s %s %s", sql_field, direction, nulls or SQL("NULLS LAST"))

        return super()._order_field_to_sql(alias, field_name, direction, nulls, query)
