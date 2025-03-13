from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    balance_partner_id = fields.Many2one(
        comodel_name="res.partner", compute="_compute_balance_partner_id", store=True
    )
    glo_partner_time_balance_ids = fields.One2many(
        comodel_name="glo.partner.time.balance", inverse_name="partner_id"
    )
    glo_sum_time_balance = fields.Float(
        compute="_compute_sum_time_balance", string="Summary Balance"
    )

    def ensure_balance_partner_id(self):
        """Making sure that we are dealing with company or person that has company
        where we are going to keep balance"""
        for obj in self:
            if obj.company_type == "person" and not obj.balance_partner_id:
                raise UserError(
                    _("Please, assign client to company for balance calculation!")
                )

    def create_update_balance_if_none(self, product_id):
        """Returns partner time balance, creates if not exists"""
        self.ensure_one()
        update_balance_id = (
            self.balance_partner_id.glo_partner_time_balance_ids.filtered(
                lambda balance_id: balance_id.product_id.id == product_id
            )
        )
        if not update_balance_id:
            self._compute_balance_partner_id()
            update_balance_id = (
                self.env["glo.partner.time.balance"]
                .sudo()
                .create(
                    {
                        "partner_id": self.balance_partner_id.id,
                        "product_id": product_id,
                    }
                )
            )
        return update_balance_id

    def update_partners_time_balance(self, time_update_dict):
        """Updates partners time balance, removes empty lines from history
        time_update_dict key - product_id
        time_update_dict val - update hours value"""
        self.ensure_one()
        self.ensure_balance_partner_id()
        for product_id, upd_hours in time_update_dict.items():
            partner_balance_id = self.create_update_balance_if_none(product_id)
            update_balance_history_id = False
            from_model_id = self._context.get("from_model_id")
            if from_model_id:
                update_balance_history_id = (
                    partner_balance_id.balance_history_ids.filtered(
                        lambda history_id: history_id.model_model == from_model_id._name
                        and history_id.res_id == from_model_id.id
                    )
                )
            if update_balance_history_id:
                update_balance_history_id.ensure_one()
                if upd_hours == 0:
                    update_balance_history_id.sudo().unlink()
                else:
                    update_balance_history_id.write(
                        {
                            "time_balance_addition": upd_hours,
                        }
                    )
            else:
                self._compute_balance_partner_id()
                from_model_create_dict_vals = {}
                if from_model_id:
                    from_model_create_dict_vals = {
                        "model_model": from_model_id._name,
                        "res_id": from_model_id.id,
                    }
                self.env["glo.partner.time.balance.history"].sudo().create(
                    {
                        **from_model_create_dict_vals,
                        "time_balance_addition": upd_hours,
                        "partner_time_balance_id": partner_balance_id.id,
                    }
                )

    def action_redirect_to_company_balance(self):
        """Redirects to time balance table of company"""
        self.ensure_one()
        self._compute_balance_partner_id()
        if self.balance_partner_id:
            return {
                "name": _("%s Time Balance", self.balance_partner_id.name),
                "view_mode": "tree, form",
                "res_model": "glo.partner.time.balance",
                "domain": [("partner_id", "=", self.balance_partner_id.id)],
                "views": [
                    (
                        self.env.ref(
                            "helpdesk_timesheet_subscription.helpdesk_timesheet"
                            "_subscription_glo_partner_time_balance_tree"
                        ).id,
                        "tree",
                    ),
                    (
                        self.env.ref(
                            "helpdesk_timesheet_subscription.helpdesk_timesheet"
                            "_subscription_glo_partner_time_balance_form"
                        ).id,
                        "form",
                    ),
                ],
                "type": "ir.actions.act_window",
                "context": {"default_partner_id": self.id},
            }
        return False

    def _compute_sum_time_balance(self):
        """Computes balance of all support time to show it on user page"""
        self.ensure_one()
        sum_balance = 0
        self._compute_balance_partner_id()
        for (
            glo_partner_time_balance_id
        ) in self.balance_partner_id.glo_partner_time_balance_ids:
            sum_balance += glo_partner_time_balance_id.time_balance
        self.glo_sum_time_balance = sum_balance

    @api.onchange("parent_id")
    def _compute_balance_partner_id(self):
        """Returns company that has to store time balance"""
        for obj in self:
            if obj.company_type == "company":
                obj.balance_partner_id = obj.id
                continue
            if obj.parent_id and obj.parent_id.company_type == "company":
                obj.balance_partner_id = obj.parent_id.id
