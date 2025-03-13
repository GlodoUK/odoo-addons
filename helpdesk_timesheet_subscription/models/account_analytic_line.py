from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    glo_log_time_id = fields.Many2one(
        comodel_name="product.product",
        domain="[('is_time_replenisher', '=', True),"
        " ('detailed_type', '=', 'service'),"
        " ('sale_ok', '=', True)]",
        string="Log Time",
    )

    @api.onchange("employee_id")
    def _set_default_employee_log_time(self):
        """Returns company that has to store time balance"""
        for obj in self:
            if obj.employee_id and obj.employee_id.glo_default_log_time_id:
                obj.glo_log_time_id = obj.employee_id.glo_default_log_time_id.id
            else:
                obj.glo_log_time_id = False

    def restrict_from_changing_ticket_and_tasks(self, vals):
        """Checks if user is changing ticket or task and restricts it
        to ease calculation"""
        for obj in self:
            if (
                obj.helpdesk_ticket_id
                and "helpdesk_ticket_id" in vals
                and vals.get("helpdesk_ticket_id") != obj.helpdesk_ticket_id.id
            ):
                raise UserError(
                    _("You can not change ticket in timesheet, please create new one.")
                )
            if (
                obj.task_id
                and "task_id" in vals
                and vals.get("task_id") != obj.task_id.id
            ):
                raise UserError(
                    _("You can not change task in timesheet, please create new one.")
                )

    def get_task_helpdesk_model(self, vals):
        """Returns models we are interested in that are connected to timesheet"""
        self.ensure_one()
        model_id = False
        if self.helpdesk_ticket_id:
            model_id = self.helpdesk_ticket_id
        elif vals.get("helpdesk_ticket_id"):
            model_id = (
                self.env["helpdesk.ticket"]
                .sudo()
                .browse(vals.get("helpdesk_ticket_id"))
            )
        elif self.task_id:
            model_id = self.task_id
        elif vals.get("task_id"):
            model_id = self.env["project.task"].sudo().browse(vals.get("task_id"))
        return model_id

    def prepare_model_and_update_dict(self, vals):
        """Returns model connected to timesheet and update value for time balance"""
        self.ensure_one()
        time_update_dict = False
        model_id = self.get_task_helpdesk_model(vals)
        if model_id:
            if model_id._name == "helpdesk.ticket":
                if model_id.team_id:
                    model_id.ensure_has_team_n_product()
                    time_update_dict = {
                        model_id.team_id.glo_product_id.id: -vals.get("unit_amount")
                    }
            elif model_id._name == "project.task":
                if self.glo_log_time_id:
                    time_update_dict = {
                        self.glo_log_time_id.id: -vals.get("unit_amount")
                    }
        return model_id, time_update_dict

    def ensure_has_customer(self, model_id):
        """Makes sure that ticket or task have customer set up"""
        self.ensure_one()
        if not model_id.partner_id:
            raise UserError(
                _("You have to set up customer for '%(model_name)s'")
                % {"model_name": model_id.name}
            )

    def update_balance_and_history(self, vals):
        """Calls functions to consolidate and validate data and
        updates partner balance"""
        for obj in self:
            obj.restrict_from_changing_ticket_and_tasks(vals)
            model_id, time_update_dict = obj.prepare_model_and_update_dict(vals)
            obj.ensure_has_customer(model_id)
            if model_id and time_update_dict:
                model_id.partner_id._compute_balance_partner_id()
                model_id.partner_id.balance_partner_id.with_context(
                    from_model_id=obj
                ).update_partners_time_balance(time_update_dict)

    @api.model
    def create(self, vals):
        """Updates history for tickets or tasks"""
        res = super().create(vals)
        if "helpdesk_ticket_id" in vals or "task_id" in vals:
            if "unit_amount" in vals:
                res.update_balance_and_history(vals)
        return res

    def write(self, vals):
        """Updates history for tickets or tasks"""
        if "unit_amount" in vals:
            self.update_balance_and_history(vals)
        result = super().write(vals)
        return result

    def unlink(self):
        """Triggers history items to remove themselves for tickets or tasks"""
        for obj in self:
            if obj.helpdesk_ticket_id or obj.task_id:
                obj.unit_amount = 0
        res = super().unlink()
        return res
