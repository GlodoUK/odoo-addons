import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

FILTER_FIELDS = [
    ("title", "Title"),
    ("summary", "Summary"),
    ("category", "Category"),
    ("author", "Author"),
    ("link", "Link"),
]


class RssFeedFilter(models.Model):
    _name = "rss.feed.filter"
    _description = "RSS Feed Filter Rule"
    _order = "sequence, id"

    feed_id = fields.Many2one("rss.feed", ondelete="cascade", index=True, required=True)
    company_id = fields.Many2one(
        related="feed_id.company_id", store=True, index=True, string="Company"
    )
    sequence = fields.Integer(default=10)
    field = fields.Selection(FILTER_FIELDS, required=True, default="title")
    pattern = fields.Char(
        required=True,
        help="Case-insensitive regular expression matched against the chosen field.",
    )

    @api.constrains("pattern")
    def _check_pattern(self):
        for rule in self:
            try:
                re.compile(rule.pattern)
            except re.error as error:
                raise ValidationError(
                    self.env._("Invalid filter pattern: %s", error)
                ) from error

    def _matches(self, item):
        """Return whether a parsed item dict matches this rule's pattern."""
        self.ensure_one()
        value = str(item.get(self.field) or "")
        return bool(re.search(self.pattern, value, re.IGNORECASE))
