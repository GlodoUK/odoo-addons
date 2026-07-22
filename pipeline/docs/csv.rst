Worked example: pick up, group, fan out
=======================================

Here is a complete integration: pick a CSV up off a filesystem, group its rows
by their first column, and hand each group to its own background job.

``_pickup`` claims the file (so a second poll cannot re-read it), parses it, and
returns one entry per group. ``expand()`` then turns each entry into an
independent ``_handle_group`` job::

    import fsspec

    from odoo import models
    from odoo.addons.pipeline import tools


    class SupplierFeed(models.Model):
        _name = "supplier.feed"
        _inherit = "pipeline.mixin"

        def import_feed(self):
            pipeline = self.pipeline()
            return pipeline.path(
                pipeline.with_delay()._pickup().expand(),
                pipeline.with_delay()._handle_group(),
            )

        def _pickup(self, message):
            # A real addon resolves the filesystem from stored connection
            # settings; built inline here for illustration.
            fs = fsspec.filesystem("sftp", host="feeds.example.com")
            groups = {}
            for path in tools.files.sweep(fs, "/in/*.csv", "/in/processed"):
                with fs.open(path, "rb") as handle:
                    rows = tools.codec_for(path).read_rows(handle)
                for row in rows:
                    key = next(iter(row.values()))  # group by the first column
                    groups.setdefault(key, []).append(row)
            # Each value becomes one job argument, so keep it JSON-serialisable.
            return [{"key": key, "rows": rows} for key, rows in groups.items()]

        def _handle_group(self, group):
            # Runs as its own queue.job: every row that shared a first column.
            self._ingest(group["key"], group["rows"])

Start it from a button or cron, exactly like any other pipeline::

    feed.import_feed().run()

A few nice things fall out for free:

* An empty drop folder means ``_pickup`` returns ``[]``, so no successor jobs
  are created and an idle poll quietly does nothing.
* A group too large for one job can be split again: return
  ``tools.batch.batched(rows, 500)`` from a stage and ``expand()`` it onto a
  per-chunk stage.
