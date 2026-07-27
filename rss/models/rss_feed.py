from datetime import timedelta

import requests
from markupsafe import Markup

from odoo import api, fields, models

from ..steps.poll import parse_feed

_TIMEOUT = 30
_USER_AGENT = "odoo-rss/1.0"


class RssFeed(models.Model):
    _name = "rss.feed"
    _description = "RSS Feed"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    url = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        index=True,
    )
    filter_ids = fields.One2many("rss.feed.filter", "feed_id", string="Filters")
    item_ids = fields.One2many("rss.item", "feed_id", string="Items")
    item_count = fields.Integer(compute="_compute_item_count")
    last_fetch = fields.Datetime(readonly=True)
    archived_retention_days = fields.Integer(
        string="Delete Archived After (Days)",
        default=0,
        help=(
            "Automatically delete archived items that have not changed for this "
            "many days. Set to 0 to keep archived items indefinitely."
        ),
    )

    _url_uniq = models.Constraint(
        "unique(url, company_id)",
        "This feed URL already exists for this company.",
    )

    def _poll(self):
        self.ensure_one()
        return self._store(self._download())

    def action_poll(self):
        for feed in self:
            feed._poll()
        return True

    def action_view_items(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("rss.rss_item_action")
        action["domain"] = [("feed_id", "=", self.id)]
        action["context"] = {"default_feed_id": self.id}
        return action

    @api.model
    def _cron_poll(self):
        for feed in self.search([("active", "=", True)]):
            feed._poll()

    @api.autovacuum
    def _gc_archived_items(self):
        for feed in self.search([("archived_retention_days", ">", 0)]):
            feed._vacuum_archived_items()

    def _vacuum_archived_items(self):
        """Delete this feed's archived items untouched past the retention window."""
        self.ensure_one()
        if self.archived_retention_days <= 0:
            return
        cutoff = fields.Datetime.now() - timedelta(days=self.archived_retention_days)
        stale = (
            self.env["rss.item"]
            .with_context(active_test=False)
            .search(
                [
                    ("feed_id", "=", self.id),
                    ("active", "=", False),
                    ("write_date", "<", cutoff),
                ]
            )
        )
        stale.unlink()

    def _download(self):
        self.ensure_one()
        response = requests.get(
            self.url,
            timeout=_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
        return response.text

    def _store(self, raw):
        self.ensure_one()
        first_fetch = not self.last_fetch
        created = self._store_items(self._filter_items(parse_feed(raw)))
        self.last_fetch = fields.Datetime.now()
        # Skip the initial import so followers are not flooded on a new feed.
        if created and not first_fetch:
            self._notify_new_items(created)
        return True

    def _notify_new_items(self, items):
        """Post a digest of newly stored items to notify the feed's followers."""
        self.ensure_one()
        entries = Markup().join(
            Markup("<li>%s</li>") % self._item_notification_label(item)
            for item in items
        )
        body = Markup("<p>%(count)s new item(s):</p><ul>%(entries)s</ul>") % {
            "count": len(items),
            "entries": entries,
        }
        self.message_post(
            body=body,
            subject=self.env._("New items in %s", self.display_name),
            subtype_xmlid="mail.mt_comment",
        )

    def _item_notification_label(self, item):
        label = item.title or item.guid or self.env._("(untitled)")
        if item.link:
            return Markup(
                '<a href="%s" target="_blank" rel="noreferrer noopener">%s</a>'
            ) % (
                item.link,
                label,
            )
        return label

    def _filter_items(self, items):
        """Keep items matching at least one rule; keep everything when unfiltered."""
        self.ensure_one()
        rules = self.filter_ids
        if not rules:
            return items
        return [item for item in items if any(rule._matches(item) for rule in rules)]

    def _compute_item_count(self):
        counts = dict(
            self.env["rss.item"]._read_group(
                [("feed_id", "in", self.ids)],
                groupby=["feed_id"],
                aggregates=["__count"],
            )
        )
        for feed in self:
            feed.item_count = counts.get(feed, 0)

    def _store_items(self, items):
        """Store unseen parsed items and return the created recordset."""
        self.ensure_one()
        # Include archived items so re-polling never recreates a seen GUID.
        seen = set(self.with_context(active_test=False).item_ids.mapped("guid"))
        vals_list = []
        for item in items:
            guid = item.get("guid")
            if not guid or guid in seen:
                continue
            vals_list.append(
                {
                    "feed_id": self.id,
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "guid": guid,
                    "published": item.get("published"),
                    "summary": item.get("summary"),
                    "category": item.get("category"),
                    "author": item.get("author"),
                }
            )
            seen.add(guid)
        return self.env["rss.item"].create(vals_list)
