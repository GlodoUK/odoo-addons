========
base_etl
========

Building blocks and conventions for file-based ETL integrations in Odoo.

Most of our integrations are the same brief: *pick up this file, transform the
rows, create these records* - specific to one customer, and changing often.
``base_etl`` is what that brief needs and no more: a handful of small,
Odoo-free helpers you *call*, plus a documented set of happy defaults for how
to wire the rest together with ordinary Odoo. There is no framework to plug
into, no DSL, no stored workflow definitions, and no ``connector`` component
registry to learn.

The helpers
-----------

All live at the top level of the package and take their dependencies
explicitly (a filesystem, a file handle), so they are unit-testable with no
Odoo env:

* ``base_etl.files`` - drive an fsspec filesystem: ``glob``, ``archive``, and
  ``sweep`` (glob + archive in one shot - the "claim the batch" primitive that
  takes files out of the drop folder before anything downstream runs, so an
  overlapping poll can never pick one up twice). ``fsspec_providers()`` lists
  the installed transports as ``Selection`` pairs.
* ``base_etl.csv`` / ``base_etl.xls`` / ``base_etl.xlsx`` - row codecs sharing
  one interface: ``read_rows(handle) -> list[dict]`` and
  ``write_rows(handle, rows)``, keyed on the header row. ``base_etl.codec_for``
  picks one by file extension, so a single call site drives any format.
* ``base_etl.batch`` - ``batched``, splitting a large parsed set into chunks
  small enough to be one downstream job's payload.

::

    from odoo.addons import base_etl

    def _import_drop_folder(self):
        fs = self._fs()                                   # you own the fsspec fs
        for path in base_etl.files.sweep(fs, "/in/*.csv", "/in/processed"):
            with fs.open(path, "rb") as handle:
                rows = base_etl.codec_for(path).read_rows(handle)
            for chunk in base_etl.batch.batched(rows, 500):
                self.with_delay()._import_rows(chunk)     # queue_job fan-out

The conventions (the happy defaults)
-------------------------------------

The helpers are only half of it. The rest is a pattern we recommend rather than
enforce - the point is to reach for these instead of building another
framework:

* **fsspec at the filesystem boundary.** Anything that touches files should go
  through an fsspec filesystem rather than ``open()`` or a protocol-specific
  client. A step written against fsspec is transport-agnostic: local today,
  SFTP or S3 tomorrow, with no code change - just a different filesystem handed
  in. The ``files`` helpers assume this.

* **petl for transforms.** For anything past "read rows / write rows" - joins,
  cuts, reshaping, type coercion, aggregation - reach for `petl
  <https://petl.readthedocs.io/>`_ and call its API directly. It works on the
  same iterables-of-dicts the codecs produce. Do *not* wrap it behind a
  ``base_etl`` shim; a second API to learn is exactly the framework we are
  avoiding.

* **queue_job for async.** When work should run in the background or fan out,
  use OCA ``queue_job``'s ``with_delay()`` directly. One job per chunk gives
  bounded, retryable units of work. base_etl does not wrap or hide it.

* **Logic in methods, configuration in fields.** Keep behaviour in ordinary
  Python methods (reviewed, tested, in git) and pure functions in a ``steps/``
  module. Keep genuine configuration - credentials, paths, schedules, filters -
  in ordinary fields. Resist ``code`` fields and ``safe_eval`` snippets:
  database code never sees git, drifts between environments, and lets anyone
  who can write the record run code inside Odoo.

* **Triggers are ordinary Odoo.** Buttons, crons, webhooks and inbound email
  all belong to the concrete integration, using standard facilities. See
  ``docs/walkthrough.rst`` for a complete file-based example (pick up, group,
  fan out), and the ``rss`` addon for the model/cron shape end to end.

Known limitations
-----------------

The row codecs materialise: ``read_rows`` returns a ``list[dict]`` (the CSV
handle is read whole; the ``.xls``/``.xlsx`` workbook is loaded in full, even
though ``xlsx`` streams internally). That suits the intended "read, chunk with
``batched``, fan each chunk out to its own job" model, where no single job
holds everything. A file too large to sit in memory at once should be split
before it reaches a codec, or read by the caller in a streaming pass -
base_etl does not offer a streaming row iterator today.

Why not a framework?
--------------------

**...the OCA ``connector`` framework?** ``connector`` earns its keep on large,
bidirectional, high-volume syncs against a stable external API - an
e-commerce connector with many record types, durable external-id bindings and
mappings that rarely change. It pays for that with real machinery: a component
registry (``_collection`` / ``_apply_on`` / ``_usage``), a binding (shadow)
model per synced record, and mapper/synchroniser layers. The cost of that
machinery is indirection - to answer "what runs when a file arrives?" you trace
component discovery instead of reading a method - and it only amortises when
the integration is big, bidirectional and long-lived. Ours usually are not:
one customer, one-directional "read this file, create these records", changing
often, and needing no durable binding. For that shape the framework is nearly
all ceremony, and the one part we genuinely want - ``queue_job`` - we can use
directly, without the component/binding/mapper layers stacked on top. So
base_etl deliberately depends on neither ``connector`` nor its component
system.

**...connector_edi?** Our EDI framework is a great fit for standardised,
high-volume EDI - backends, bindings, mappers and exchange records moving
through a formal lifecycle. Most integrations simply are not that, and
modelling them as exchange types and mappers adds ceremony the job never
needed while spreading one integration across so many registered pieces that
"what happens when a file arrives?" gets hard to answer. When a job really is
strict EDI, reach for ``connector_edi``; the rest of the time, base_etl keeps
out of the way.

**...a pipeline DSL?** An earlier iteration described integrations as a graph
of stages. It turned out the graph only ever expressed a linear chain, on top
of proxy magic and a silent-``None`` footgun, and everything it did reduced to
a few lines of direct ``queue_job``. The helpers survived that experiment; the
DSL did not. base_etl is the helpers plus the conventions, nothing more.
