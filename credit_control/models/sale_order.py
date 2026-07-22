from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    skip_credit_control_rules = fields.Boolean(
        "Allow Credit Control Bypass",
        copy=False,
    )

    credit_control_hold = fields.Many2one(
        "mail.activity",
    )

    def action_confirm(self):
        for order in self:
            order._check_credit_control(events=["confirm"])

        return super(
            SaleOrder, self.with_context(skip_check_credit_control=True)
        ).action_confirm()

    def _action_cancel(self):
        if self.credit_control_hold:
            self.credit_control_hold.unlink()
        return super()._action_cancel()

    def _check_credit_control(self, events=None):
        self.ensure_one()

        if not events:
            events = ["confirm_edit", "confirm"]

        if self._context.get("skip_check_credit_control", False):
            return

        if self._context.get("website_order_tx", False):
            return

        if "website_id" in self._fields and self.website_id:
            return

        partner_id = self.partner_id.sudo().commercial_partner_id
        policy_id = partner_id.credit_control_policy_id
        if not policy_id:
            policy_id = (
                self.env["credit.control.policy"]
                .sudo()
                .search([("default", "=", True)], limit=1)
            )

        if policy_id and self.skip_credit_control_rules:
            if (
                policy_id.action_bypass_users
                and self.env.user in policy_id.action_bypass_users
            ):
                return
            if (
                policy_id.action_bypass_groups
                and self.env.user.groups_id & policy_id.action_bypass_groups
            ):
                return

        if policy_id:
            return policy_id.check_rules(events, partner_id, self)

    def action_release_hold(self):
        for order in self:
            policy_id = (
                order.partner_id.sudo().commercial_partner_id.credit_control_policy_id
            )
            if not policy_id:
                order.credit_control_hold.unlink()
                continue
            if order.credit_control_hold:
                if (
                    policy_id.action_bypass_users
                    and self.env.user in policy_id.action_bypass_users
                ):
                    order.credit_control_hold.unlink()
                    continue
                if (
                    policy_id.action_bypass_groups
                    and self.env.user.groups_id & policy_id.action_bypass_groups
                ):
                    order.credit_control_hold.unlink()
                    continue
                raise UserError(
                    self.env._("You are not allowed to release this order from hold.")
                )

    def write(self, vals):
        """
        Maintaining the SOs on credit hold after update if before them was in
        """
        before = {}

        for order in self:
            before[order] = (order.amount_total, len(order.order_line))

        res = super().write(vals)

        for order in self.filtered(
            lambda r: (
                r.state in ("sale", "done", "reserved")
                and (before[r][0] < r.amount_total or len(r.order_line) != before[r][1])
            )
        ):
            # total_increase = order.amount_total - before[order][1]
            order._check_credit_control(events=["confirm_edit", "edit"])

        return res
