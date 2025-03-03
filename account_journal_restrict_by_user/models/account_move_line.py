from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    restricted_user_ids = fields.Many2many(
        related="move_id.journal_id.restricted_user_ids",
    )

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

        if self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            args += [
                ("move_id.journal_id.restricted_user_ids", "in", self.env.user.ids)
            ]

        return super()._search(args, offset, limit, order, count, access_rights_uid)

    def read(self, fields=None, load="_classic_read"):
        if fields is None:
            fields = []

        if (
            self.env.user.has_group(
                "account_journal_restrict_by_user.group_restrict_account_journal"
            )
            and "journal_id" not in fields
        ):
            fields += ["journal_id"]

        move_lines = super().read(fields=fields, load=load)
        if self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            allowed_journals = self.env["account.journal"].search(
                [("restricted_user_ids", "in", self.env.user.ids)]
            )

            for line in move_lines:
                if line["journal_id"][0] not in allowed_journals.ids:
                    raise AccessError(_("You are not allowed to access this journal."))

        return move_lines

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if not domain:
            domain = []

        if self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            domain += [
                ("move_id.journal_id.restricted_user_ids", "in", self.env.user.ids)
            ]

        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
