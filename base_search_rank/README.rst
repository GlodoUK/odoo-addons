================
base_search_rank
================

Ranked substring + fuzzy searching as a custom field type, built on pg_trgm
word similarity.

The problem: searching ``967`` should return both ``sku=967`` and
``sku=aaa967bb``, with the exact match first — and ``candel`` should still
find candles. Plain ``ilike`` gets the recall but not the ranking or the
misspellings; this module provides both.

One ``SearchRank`` field is both the searchable document and the search
driver: it computes its own content from the declared ``sources``, and
supplies the behaviour through the ORM's own per-field hooks: domain
conditions on it expand to substring OR fuzzy matching
(``Field.determine_domain``), and its ``rank`` property renders a relevance
expression for ordering (``Field.property_to_sql``). No mixin, no model
overrides, no manual compute to drift out of sync; all configuration is
code.

This is deliberately not OCA's ``base_search_fuzzy``: that module only adds
a whole-string ``%`` similarity operator (which misses short codes against
long texts entirely) with no ranking, configures its indexes through DB
records, and its expression monkey-patch has no target in Odoo 19.

Usage
=====

Declare what is searchable::

    from odoo.addons.base_search_rank.fields import SearchRank

    class ProductProduct(models.Model):
        _inherit = "product.product"

        search_rank = SearchRank(
            sources=("=default_code", "barcode", "product_tmpl_id.name"),
        )

The field computes its own document from ``sources`` (dotted paths allowed,
concatenated in declaration order; translated fields contribute every
installed language) and recomputes when they change. ``store=True`` and
``index='trigram'`` are forced — Odoo 19 natively builds the
``unaccent(...) gin_trgm_ops`` GIN index, which serves both match arms.

A leading ``=`` (mirroring Odoo's ``=like``) marks an exact source: its
whole-value (case/accent-insensitive) match with the term outranks any
similarity score — typically the code/SKU field. Because an exact source
is part of the document like any other source, its matches are always
findable; there is no separate list to drift out of sync. There is also
deliberately no custom-compute option — that split is exactly where the
document and the ranking would drift apart; subclass and override
``_compute_from_sources`` for special document needs.

Then::

    from odoo.addons.base_search_rank.utils import search_ranked

    search_ranked(env["product.product"], "967", limit=20)

returns records matched by substring *or* fuzzy word similarity, ordered
best-first: whole-value ``default_code`` matches score 2.0, above any
``word_similarity()`` score against the document.

The field composes with the standard ORM everywhere:

- ``[('search_rank', 'ilike', term)]`` is a normal domain condition, usable
  anywhere — including dropping ``<field name="search_rank"/>`` into a
  search view for fuzzy matching from the search bar (matching only; a
  search view cannot inject ordering).
- ``order='search_rank.rank desc'`` ranks any search() by relevance,
  whenever the term is in context as ``search_rank_term``
  (``search_ranked()`` arranges both).

For UI integration, inherit ``base_search_rank.mixin`` alongside the
model::

    class ProductProduct(models.Model):
        _name = "product.product"
        _inherit = ["product.product", "base_search_rank.mixin"]

It wires two things, both inert until used:

- ``name_search`` returns ranked + fuzzy suggestions when opted in per m2o
  field, per view, via the field's ``context`` attribute (the same plumbing
  core uses for ``partner_id`` on product fields)::

      <field name="product_id" context="{'search_rank_enable': True}"/>

  Everything else — including programmatic callers using ``name_search`` as
  a conservative matcher, where fuzzy must not turn "not found" into a
  plausible wrong record — stays stock. Cross-model domain resolution
  (``('product_id', 'ilike', 'foo')`` on other models) does not pass
  through ``name_search`` at all, so the blast radius is opted-in dropdowns
  and direct callers only.

- ``_search`` orders by relevance whenever the domain contains a condition
  on a SearchRank field (e.g. a search-view facet on it); the caller's
  order becomes the tiebreak within equal ranks. Other searches are
  untouched.

Notes
=====

- ``=``-marked sources must be direct stored fields on the model (the rank
  SQL is built against the model's own table, without joins). The boost
  compares the term against the live column (whole-value,
  case/accent-insensitive), not the document.
- The fuzzy cutoff is a per-field parameter (``SearchRank(sources=...,
  threshold=0.5)``, default 0.4), applied per-transaction via
  ``set_config``; the postgres default of 0.6 rejects common misspellings
  ("candel" -> "candle" scores 0.571), while lower values admit more noise
  — which ranking keeps at the bottom.
- ``pre_init_hook`` creates the pg_trgm extension (or fails install with
  instructions if it lacks permission).
- Reading the field yields the document text (handy for debugging what is
  actually searchable).
- Always order by ``search_rank.rank``; ordering by the bare field name
  sorts by document text. Without ``search_rank_term`` in context the rank
  renders as a constant. Neither is valid in ``_read_group`` ordering.
- The field's matching replaces core ``ilike`` SQL for conditions on it
  (substring semantics are preserved; both sides are unaccented like core).
