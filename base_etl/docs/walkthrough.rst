Worked example: pick up, group, fan out
=======================================

A complete file-based integration, with no framework: an ordinary Odoo model,
OCA ``queue_job`` for the background work, and ``base_etl`` for the IO. It picks
CSVs up off a filesystem, groups each file's rows by their first column, and
hands every group to its own background job.

The consuming addon depends on ``base_etl`` and ``queue_job`` (and inherits
``queue.job``'s ``with_delay`` however your project does). Nothing here inherits
a ``base_etl`` mixin -- the helpers are called, not plugged into::

    import fsspec

    from odoo import fields, models

    from odoo.addons import base_etl


    class SupplierFeed(models.Model):
        _name = "supplier.feed"

        protocol = fields.Selection(
            selection=lambda self: [("disabled", "Disabled")]
            + base_etl.files.fsspec_providers(),
            required=True,
        )
        host = fields.Char()
        # ... plus whatever credentials/paths the protocol needs.

        def action_import(self):
            # The pickup itself runs in the background, so a button or cron
            # returns immediately.
            for feed in self:
                feed.with_delay()._pickup()
            return True

        def _fs(self):
            # Build the fsspec filesystem from stored settings. fsspec caches
            # filesystem instances, so calling this per job is cheap.
            self.ensure_one()
            return fsspec.filesystem(self.protocol, host=self.host)

        def _pickup(self):
            fs = self._fs()
            # sweep() claims the whole batch first -- files are moved out of the
            # drop folder before anything downstream runs, so an overlapping
            # cron can never pick one up twice.
            for path in base_etl.files.sweep(fs, "/in/*.csv", "/in/processed"):
                with fs.open(path, "rb") as handle:
                    rows = base_etl.codec_for(path).read_rows(handle)
                groups = {}
                for row in rows:
                    key = next(iter(row.values()))  # group by the first column
                    groups.setdefault(key, []).append(row)
                for key, group in groups.items():
                    # Each argument is stored as a job argument, so keep it
                    # JSON-serialisable.
                    self.with_delay()._handle_group(key, group)

        def _handle_group(self, key, rows):
            # Runs as its own queue.job: every row that shared a first column.
            self._ingest(key, rows)

Trigger it like any other model method -- a button (``action_import`` above) or
a cron::

    <record id="ir_cron_import_feeds" model="ir.cron">
        <field name="name">Supplier feeds: import</field>
        <field name="model_id" ref="model_supplier_feed" />
        <field name="state">code</field>
        <field name="code">model.search([]).action_import()</field>
        <field name="interval_number" eval="15" />
        <field name="interval_type">minutes</field>
    </record>

A few nice things fall out of writing it this way:

* **Atomic claim.** ``sweep`` and the ``with_delay`` enqueues happen in one
  transaction, so if ``_pickup`` raises, the file moves roll back *and* no
  group jobs are enqueued -- nothing is half-done.
* **Idle polls do nothing.** An empty drop folder means ``sweep`` returns
  ``[]``, the loop never runs, and no jobs are created.
* **Big groups split again.** A group too large for one job is chunked -- wrap
  it in ``base_etl.batch.batched(group, 500)`` and enqueue one
  ``_handle_group`` per chunk, so every job carries a bounded payload.
* **Format-agnostic.** ``codec_for`` picks the reader by extension, so the same
  ``_pickup`` handles a ``.csv`` or ``.xlsx`` drop with no change.
