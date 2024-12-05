from odoo import _, api, fields, models

class AccountInovice(models.Model):
    _inherit = "account.invoice"

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        if self.env.context.get("sales_person_invoice_no_follow"):
            return []
        return super(AccountInovice, self)._message_auto_subscribe_followers(updated_values, default_subtype_ids)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        return super(SaleOrder, self.with_context(sales_person_invoice_no_follow=True)).action_invoice_create(grouped, final)
