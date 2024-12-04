import itertools

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, format_date


class LeaseSchedule(models.Model):
    _name = "sale_lease_stock.lease.schedule"
    _description = "Lease Payment Schedule"

    # TODO: compute a name and then use it on the invoice. it should include
    # client_order_ref, SO, etc.
    # TODO: group invoices by partner_invoice_id?

    partner_id = fields.Many2one(related="order_id.partner_id", required=True)
    partner_invoice_id = fields.Many2one(
        related="order_id.partner_invoice_id",
        required=True,
    )
    line_id = fields.Many2one("sale.order.line", required=True, index=True)
    order_id = fields.Many2one(related="line_id.order_id", store=True)
    date = fields.Date(required=True)
    price = fields.Monetary(required=True)
    quantity_to_invoice = fields.Float()
    currency_id = fields.Many2one("res.currency", required=True)
    account_move_line_ids = fields.One2many("account.move.line", "lease_schedule_id")
    invoice_count = fields.Integer(compute="_compute_invoice_count")
    state = fields.Selection(
        [
            ("cancel", "Cancelled"),
            ("pending", "Pending"),
            ("done", "Done"),
        ],
        default="pending",
        compute="_compute_state",
        store=True,
    )
    company_id = fields.Many2one(related="order_id.company_id", store=True)
    cancelled_at = fields.Datetime()

    @api.depends("account_move_line_ids")
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.account_move_line_ids.mapped("move_id"))

    @api.depends("account_move_line_ids.move_id.state", "cancelled_at")
    def _compute_state(self):
        for record in self:
            if record.cancelled_at:
                record.state = "cancel"
                continue

            qty_invoiced = 0.0
            for invoice_line in record.account_move_line_ids:
                if invoice_line.move_id.state != "cancel":
                    if invoice_line.move_id.move_type == "out_invoice":
                        qty_invoiced += invoice_line.quantity
                    elif invoice_line.move_id.move_type == "out_refund":
                        qty_invoiced -= invoice_line.quantity

            if (
                float_compare(
                    qty_invoiced,
                    record.quantity_to_invoice,
                    precision_rounding=record.line_id.product_uom.rounding,
                )
                >= 0
            ):
                record.state = "done"
                continue

            record.state = "pending"

    def action_cancel(self):
        for record in self:
            if record.state != "pending":
                raise UserError(_("Cannot cancel a schedule that is not pending"))
            record.cancelled_at = fields.Datetime.now()

    def _get_invoice_vals(self):
        self.ensure_one()

        journal = (
            self.env["account.move"]
            .with_context(default_move_type="out_invoice")
            ._get_default_journal()
        )
        if not journal:
            raise UserError(
                _("Please define an accounting sales journal for the company %s (%s).")
                % (self.order_id.company_id.name, self.order_id.company_id.id)
            )

        invoice_vals = {
            "ref": self.order_id.client_order_ref or "",
            "move_type": "out_invoice",
            "currency_id": self.currency_id.id,
            "campaign_id": self.order_id.campaign_id.id,
            "medium_id": self.order_id.medium_id.id,
            "source_id": self.order_id.source_id.id,
            "user_id": self.order_id.user_id.id,
            "invoice_user_id": self.order_id.user_id.id,
            "team_id": self.order_id.team_id.id,
            "partner_id": self.partner_invoice_id.id,
            "partner_shipping_id": self.order_id.partner_shipping_id.id,
            "fiscal_position_id": (
                self.order_id.fiscal_position_id
                or self.order_id.fiscal_position_id.get_fiscal_position(
                    self.partner_invoice_id.id
                )
            ).id,
            "partner_bank_id": self.order_id.company_id.partner_id.bank_ids[:1].id,
            "journal_id": journal.id,  # company comes from the journal
            "invoice_origin": self.order_id.name,
            "invoice_payment_term_id": self.order_id.payment_term_id.id,
            "payment_reference": self.order_id.reference,
            "invoice_line_ids": [(0, 0, self._get_invoice_line_vals())],
            "company_id": self.order_id.company_id.id,
        }
        return invoice_vals

    def _get_invoice_line_vals(self):
        self.ensure_one()
        order_id = self.line_id.order_id
        sale_name = order_id.display_name
        if order_id.client_order_ref:
            sale_name = "{} ({})".format(sale_name, order_id.client_order_ref)

        name = "{sale} - {line}\nLease Period: {date}".format(
            sale=sale_name,
            line=self.line_id.product_id.display_name,
            date=format_date(self.env, self.date),
        )

        res = {
            "name": name,
            "product_id": self.line_id.product_id.id,
            "product_uom_id": self.line_id.product_uom.id,
            "quantity": self.quantity_to_invoice,
            "discount": 0.0,
            "price_unit": self.price,
            "sale_line_ids": [(4, self.line_id.id)],
            "tax_ids": [(6, 0, self.line_id.tax_id.ids)],
            "analytic_tag_ids": [(6, 0, self.line_id.analytic_tag_ids.ids)],
            "lease_schedule_id": self.id,
        }
        return res

    def _get_invoice_grouping_keys(self):
        return ["company_id", "partner_id", "currency_id"]

    def action_view_invoices(self):
        invoices = self.mapped("account_move_line_ids.move_id")

        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        return action

    def action_create_invoices(self):
        invoiceable = self.filtered(lambda l: l.state == "pending")
        invoice_grouping_keys = self._get_invoice_grouping_keys()
        invoice_vals_list = sorted(
            [record._get_invoice_vals() for record in invoiceable],
            key=lambda x: [
                x.get(grouping_key) for grouping_key in invoice_grouping_keys
            ],
        )

        new_invoice_vals_list = []
        invoice_grouping_keys = self._get_invoice_grouping_keys()
        invoice_vals_list = sorted(
            invoice_vals_list,
            key=lambda x: [
                x.get(grouping_key) for grouping_key in invoice_grouping_keys
            ],
        )
        for _grouping_keys, invoices in itertools.groupby(
            invoice_vals_list,
            key=lambda x: [
                x.get(grouping_key) for grouping_key in invoice_grouping_keys
            ],
        ):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None

            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals["invoice_line_ids"] += invoice_vals[
                        "invoice_line_ids"
                    ]
                origins.add(invoice_vals["invoice_origin"])
                payment_refs.add(invoice_vals["payment_reference"])
                refs.add(invoice_vals["ref"])

            ref_invoice_vals.update(
                {
                    "ref": ", ".join(refs)[:2000],
                    "invoice_origin": ", ".join(origins),
                    "payment_reference": len(payment_refs) == 1
                    and payment_refs.pop()
                    or False,
                }
            )
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list
        self.env["account.move"].sudo().with_context(
            default_move_type="out_invoice"
        ).create(invoice_vals_list)
        return self.action_view_invoices()

    @api.model
    def _action_cron(self):
        pending = self.search(
            [
                ("date", "<=", fields.Date.today()),
                ("state", "=", "pending"),
            ]
        )

        pending.action_create_invoices()
