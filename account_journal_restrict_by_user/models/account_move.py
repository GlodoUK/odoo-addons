from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class AccountMove(models.Model):
    _inherit = "account.move"

    restricted_user_ids = fields.Many2many(related="journal_id.restricted_user_ids")

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
        count=False,
        access_rights_uid=None,
    ):
        if not args:
            args = []

        if not self.env.su and self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            args += [("journal_id.restricted_user_ids", "in", self.env.user.ids)]

        return super()._search(args, offset, limit, order, count, access_rights_uid)

    def read(self, fields=None, load="_classic_read"):
        if fields is None:
            fields = []

        should_restrict = not self.env.su and self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        )

        if should_restrict and "journal_id" not in fields:
            fields += ["journal_id"]

        moves = super().read(fields=fields, load=load)
        if should_restrict:
            allowed_journals = self.env["account.journal"].search(
                [("restricted_user_ids", "in", self.env.user.ids)]
            )

            for move in moves:
                if move["journal_id"][0] not in allowed_journals.ids:
                    raise AccessError(_("You don't have access to this journal."))

        return moves

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if not domain:
            domain = []

        if not self.env.su and self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            domain += [("journal_id.restricted_user_ids", "in", self.env.user.ids)]

        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
