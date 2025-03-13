from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GloPartnerTimeBalance(models.Model):
    _name = "glo.partner.time.balance"
    _description = "Partner Time Balance"

    name = fields.Char(compute="_compute_balance_name")
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        ondelete="cascade",
        domain="[('is_company', '=', True)]",
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        domain="[('is_time_replenisher', '=', True),"
        " ('detailed_type', '=', 'service'),"
        " ('sale_ok', '=', True)]",
        required=True,
    )
    balance_history_ids = fields.One2many(
        comodel_name="glo.partner.time.balance.history",
        inverse_name="partner_time_balance_id",
    )

    time_balance = fields.Float()

    def _compute_balance_name(self):
        """Generates readable balance name"""
        for obj in self:
            obj.name = f"{obj.partner_id.name}/{obj.product_id.name} Balance"

    def action_redirect_to_balance_history(self):
        """Redirects to balance history"""
        self.ensure_one()
        return {
            "name": _("%(partner_name)s-%(product_name)s Time Balance History")
            % {
                "partner_name": self.partner_id.name,
                "product_name": self.product_id.name,
            },
            "view_mode": "tree",
            "res_model": "glo.partner.time.balance.history",
            "domain": [("partner_time_balance_id", "=", self.id)],
            "view_id": self.env.ref(
                "helpdesk_timesheet_subscription.helpdesk_timesheet_subscription"
                "_glo_partner_time_balance_history_tree"
            ).id,
            "type": "ir.actions.act_window",
            "context": {"default_partner_time_balance_id": self.id},
        }

    def _check_if_company(self, vals):
        """Checks if incomming vals have partner and that partner is company"""
        if (
            vals.get("partner_id")
            and self.env["res.partner"]
            .sudo()
            .browse(vals.get("partner_id"))
            .company_type
            != "company"
        ):
            raise UserError(_("You can add balance time only on company level!"))

    def _ensure_no_same_partner_product(self, vals):
        """Checks if there are no duplicate records of product for same partner"""
        if (
            "partner_id" in vals
            and "product_id" in vals
            and self.env["glo.partner.time.balance"]
            .sudo()
            .search(
                [
                    ("partner_id", "=", vals.get("partner_id")),
                    ("product_id", "=", vals.get("product_id")),
                ]
            )
        ):
            raise UserError(
                _("You can not create two balances for same product one one partner!")
            )

    def update_result_time_balance(self, history_id=False):
        """Sets time balance as it is in last history record"""
        self.ensure_one()
        if not history_id:
            history_id = self.balance_history_ids[-1]
        if not history_id:
            self.time_balance = 0
        else:
            self.time_balance = history_id.result_time_balance

    def update_history_time_balance(self):
        """Updates time balance due to last history time balance"""
        for obj in self:
            if obj.balance_history_ids:
                result_history_balance = 0
                for history_id in obj.balance_history_ids:
                    result_history_balance += history_id.time_balance_addition
                    history_id.result_time_balance = result_history_balance
                    obj.update_result_time_balance(history_id)
            else:
                obj.time_balance = 0

    @api.model
    def create(self, vals):
        """Validates if company and if we do not have same partner
        product for this company"""
        self._check_if_company(vals)
        self._ensure_no_same_partner_product(vals)
        res = super().create(vals)
        return res

    def write(self, vals):
        """Ensure we do not change partner or product in balance sheets."""
        self._check_if_company(vals)
        if "partner_id" in vals or "product_id" in vals:
            raise UserError(
                _("You can not change partner or product for any balance record!")
            )
        result = super().write(vals)
        return result

    # Can't unlink unless we delete history
