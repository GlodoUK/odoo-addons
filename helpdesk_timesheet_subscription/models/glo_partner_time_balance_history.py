from odoo import api, fields, models


class GloPartnerTimeBalanceHistory(models.Model):
    _name = "glo.partner.time.balance.history"
    _description = "Partner Time Balance History"

    name = fields.Char(compute="_compute_balance_history_name")
    partner_time_balance_id = fields.Many2one(
        comodel_name="glo.partner.time.balance", required=True
    )
    model_model = fields.Char(string="Technical Model Name", readonly=True, help="")
    res_id = fields.Integer(string="Resource ID")
    time_balance_addition = fields.Float()
    result_time_balance = fields.Float()

    def _compute_balance_history_name(self):
        """Generates model name for balance history to be more
        user friendly"""
        for obj in self:
            if obj.model_model and obj.res_id:
                record_id = self.env[obj.model_model].sudo().browse(obj.res_id)
                if record_id:
                    if record_id._name == "account.move":
                        obj.name = f"Invoice: {record_id.display_name}"
                    elif record_id._name == "account.analytic.line":
                        if record_id.helpdesk_ticket_id:
                            obj.name = (
                                f"Ticket: {record_id.helpdesk_ticket_id.display_name}"
                            )
                        elif record_id.task_id:
                            obj.name = f"""Task: {
                                record_id.task_id.project_id.name if
                                record_id.task_id.project_id else ''} /
                                {record_id.task_id.name}"""

    def get_last_created_record(self, partner_time_balance_id):
        """Gets last created record (highest ID) from history"""
        sib_history_ids = partner_time_balance_id.balance_history_ids.filtered(
            lambda history_id: history_id != self
        )
        if sib_history_ids:
            return sib_history_ids[-1]
        return False

    def calculate_result_time_balance(self, partner_time_balance_id, time_bal_add):
        """Calculates time balance regarding previous records time balance"""
        partner_time_balance_id.ensure_one()
        last_record_id = self.get_last_created_record(partner_time_balance_id)
        if last_record_id:
            return last_record_id.result_time_balance + time_bal_add
        return time_bal_add

    @api.model
    def create(self, vals):
        """Sets time balance to time balance module,
        recalculates time balance due to prev record"""
        if vals.get("time_balance_addition"):
            vals["result_time_balance"] = self.calculate_result_time_balance(
                self.env["glo.partner.time.balance"]
                .sudo()
                .browse(vals.get("partner_time_balance_id")),
                vals.get("time_balance_addition"),
            )
            res = super().create(vals)
            if "result_time_balance" in vals:
                res.partner_time_balance_id.update_result_time_balance()
            return res
        return False

    def write(self, vals):
        """Recalculates all history balances due to this balance_id"""
        result = super().write(vals)
        if not vals.get("result_time_balance"):
            self.partner_time_balance_id.update_history_time_balance()
        return result

    def unlink(self):
        """Trigger recalculation of all balances when current records are gone"""
        recalculate_balance_ids = self.env["glo.partner.time.balance"]
        for obj in self:
            if obj.partner_time_balance_id not in recalculate_balance_ids:
                recalculate_balance_ids += obj.partner_time_balance_id
        res = super().unlink()
        recalculate_balance_ids.update_history_time_balance()
        return res
