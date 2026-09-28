from odoo import api, fields, models


class RssItem(models.Model):
    _name = "rss.item"
    _description = "RSS Item"
    _inherit = ["mail.thread"]
    _order = "published desc, id desc"

    feed_id = fields.Many2one("rss.feed", ondelete="cascade", index=True, required=True)
    company_id = fields.Many2one(
        related="feed_id.company_id", store=True, index=True, string="Company"
    )
    title = fields.Char()
    link = fields.Char()
    guid = fields.Char(index=True, string="GUID")
    published = fields.Datetime()
    category = fields.Char()
    author = fields.Char()
    summary = fields.Html(sanitize=True)
    active = fields.Boolean(default=True, tracking=True, index=True)

    _guid_feed_uniq = models.Constraint(
        "unique(feed_id, guid)",
        "This item is already stored for this feed.",
    )

    @api.depends("title", "guid")
    def _compute_display_name(self):
        for item in self:
            item.display_name = item.title or item.guid or f"Item {item.id}"
