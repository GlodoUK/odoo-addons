from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _restricted_user_ids_domain(self):
        return [
            (
                "groups_id",
                "=",
                self.env.ref(
                    "account_journal_restrict_by_user.group_restrict_account_journal"
                ).id,
            )
        ]

    restricted_user_ids = fields.Many2many(
        "res.users",
        string="Restricted Users",
        help="Only users in this list can access this journal when they are a"
        ' member of the "Restrict Account Journal" group.',
        copy=True,
        domain=lambda self: self._restricted_user_ids_domain(),
        index=True,
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

        if not self.env.su and self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            args += [("restricted_user_ids", "in", self.env.user.ids)]

        return super()._search(args, offset, limit, order, count, access_rights_uid)

    def read(self, fields=None, load="_classic_read"):
        journals = super().read(fields=fields, load=load)

        if not self.env.su and self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            allowed_journals = self.env["account.journal"].search(
                [("restricted_user_ids", "in", self.env.user.ids)]
            )

            for journal in journals:
                if journal["id"] not in allowed_journals.ids:
                    raise AccessError(_("You are not allowed to access this journal."))

        return journals

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if not domain:
            domain = []

        if not self.env.su and self.env.user.has_group(
            "account_journal_restrict_by_user.group_restrict_account_journal"
        ):
            domain += [("restricted_user_ids", "in", self.env.user.ids)]
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
