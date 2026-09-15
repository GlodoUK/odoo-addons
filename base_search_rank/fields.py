from odoo import fields
from odoo.fields import Domain
from odoo.tools import SQL


def apply_word_similarity_threshold(env, threshold):
    """Set the pg_trgm fuzzy-match cutoff, scoped to the current transaction."""
    env.cr.execute(
        "SELECT set_config('pg_trgm.word_similarity_threshold', %s, true)",
        [str(threshold)],
    )


class SearchRank(fields.Text):
    """Stored searchable document with ranked substring + fuzzy search.

    One field is document and search driver. Declare what is searchable and
    the field computes the document itself::

        search_rank = SearchRank(
            sources=("=default_code", "barcode", "product_tmpl_id.name"),
        )

    ``sources`` are field names (dotted paths allowed), concatenated in
    declaration order; translated fields contribute every installed
    language. A leading ``=`` (mirroring Odoo's ``=like``) marks an exact
    source: its whole-value (case/accent-insensitive) match with the term
    outranks any similarity score — typically the code/SKU field. Exact
    sources are part of the document like any other, which is what
    guarantees their matches are found in the first place (matching only
    sees the document; ranking only reorders what matching found). They
    must be direct stored fields (the rank SQL is built without joins).

    There is deliberately no custom compute option — the document and the
    ranking must not drift apart. A model with genuinely special document
    needs should subclass and override ``_compute_from_sources``.

    ``store=True`` and ``index='trigram'`` are forced (Odoo builds the
    ``unaccent(...) gin_trgm_ops`` GIN index natively), and the field drives
    search through the ORM's per-field hooks:

    - **Matching**: any text condition on the field — ``('search_rank',
      'ilike', term)``, or the field dropped into a search view — expands
      to substring (``ILIKE``, so an embedded "967" always hits) OR pg_trgm
      word similarity (so misspellings hit).
    - **Ranking**: the ``rank`` property renders a relevance expression, so
      ``order='search_rank.rank desc'`` (with the term in context as
      ``search_rank_term``) sorts best-first through the standard ordering
      path: whole-value equality on the ``=``-marked sources scores 2.0,
      above any ``word_similarity()`` score. Without a
      term in context it renders 0.0 and orders nothing. Ordering by the
      bare field name is the document text, i.e. meaningless — always order
      by ``.rank``. Not valid as a read_group order.

    ``utils.search_ranked(model, term)`` bundles both for the common case.

    The other attribute is ``threshold`` — the fuzzy cutoff, see below.
    """

    type = "text"

    sources = ()
    # pg_trgm.word_similarity_threshold for the fuzzy match arm. The
    # postgres default (0.6) rejects classic misspellings such as
    # "candel" -> "candle" (0.571); 0.4 accepts them while ranking keeps
    # the noise it lets in at the bottom.
    threshold = 0.4

    # truthy so domain optimization routes conditions to determine_domain()
    search = True

    def _setup_attrs__(self, model_class, name):  # noqa: PLW3201
        res = super()._setup_attrs__(model_class, name)
        self.store = True
        if not self.index:
            self.index = "trigram"
        assert not isinstance(self.sources, str) and self.sources, (
            f"SearchRank field {self} requires sources=(field names,)"
        )
        assert not getattr(self, "exact", None), (
            f"SearchRank field {self}: exact= has been merged into sources;"
            " mark exact sources with a leading '=', e.g. '=default_code'"
        )
        self._source_paths = tuple(s.lstrip("=") for s in self.sources)
        self._exact_fields = tuple(s[1:] for s in self.sources if s.startswith("="))
        assert all(fname.count(".") <= 1 for fname in self._exact_fields), (
            f"SearchRank field {self}: exact sources must be direct stored"
            " fields or a single one2many hop (e.g."
            " '=product_variant_ids.default_code')"
        )
        assert not self.compute, (
            f"SearchRank field {self} computes itself from sources;"
            " subclass and override _compute_from_sources for custom needs"
        )
        self.compute = self._compute_from_sources
        self._depends = self._source_paths
        return res

    def _compute_from_sources(self, records):
        lang_codes = [code for code, _name in records.env["res.lang"].get_installed()]
        for record in records:
            values = []
            for path in self._source_paths:
                target, fname = record, path
                while "." in fname:
                    relation, fname = fname.split(".", 1)
                    target = target[relation]
                field = target._fields[fname]
                if field.translate:
                    values += [
                        value
                        for code in lang_codes
                        for value in target.with_context(lang=code).mapped(fname)
                        if value
                    ]
                else:
                    values += [str(value) for value in target.mapped(fname) if value]
            record[self.name] = " ".join(dict.fromkeys(values)) or False

    def determine_domain(self, records, operator, value):
        # `search` intercepts every condition on this field, so whatever we
        # return must not mention the field by name (it would recurse back
        # here); both match arms are emitted as custom SQL against the
        # column instead.
        if operator not in ("ilike", "like", "=ilike", "=like", "="):
            return NotImplemented
        fname = self.name
        if not isinstance(value, str) or not value.strip():
            # nullness checks, e.g. ('search_rank', '=', False)
            return Domain.custom(
                to_sql=lambda model, alias, query: SQL(
                    "%s IS NULL", model._field_to_sql(alias, fname, query)
                ),
                predicate=lambda record: not record[fname],
            )
        term = value.strip()
        apply_word_similarity_threshold(records.env, self.threshold)

        def match_to_sql(model, alias, query):
            unaccent = model.env.registry.unaccent
            sql_col = unaccent(model._field_to_sql(alias, fname, query))
            return SQL(
                "(%s ILIKE %s OR %s <%% %s)",
                sql_col,
                unaccent(SQL("%s", f"%{term}%")),
                unaccent(SQL("%s", term)),
                sql_col,
            )

        return Domain.custom(
            to_sql=match_to_sql,
            # Python-side evaluation (record rules, filtered_domain) has no
            # word_similarity; approximate with the substring arm, so
            # fuzzy-only matches are dropped rather than crashing.
            predicate=lambda record: term.lower() in (record[fname] or "").lower(),
        )

    def property_to_sql(self, field_sql, property_name, model, alias, query):
        # Renders `search_rank.rank` as a relevance score, which makes
        # order='search_rank.rank desc' work through the standard ordering
        # path. ORDER BY has no value channel of its own, so the term
        # travels in context.
        if property_name != "rank":
            return super().property_to_sql(
                field_sql, property_name, model, alias, query
            )
        term = (model.env.context.get("search_rank_term") or "").strip()
        if not term:
            return SQL("0.0")
        unaccent = model.env.registry.unaccent
        sql_term = unaccent(SQL("%s", term))
        scores = []
        for fname in self._exact_fields:
            if "." in fname:
                scores.append(
                    self._exact_score_one2many_sql(model, alias, fname, sql_term)
                )
                continue
            sql_field = unaccent(model._field_to_sql(alias, fname))
            scores.append(
                SQL("(LOWER(%s) = LOWER(%s))::int * 2.0", sql_field, sql_term)
            )
        scores.append(
            SQL("COALESCE(word_similarity(%s, %s), 0.0)", sql_term, unaccent(field_sql))
        )
        if len(scores) == 1:
            return scores[0]
        return SQL("GREATEST(%s)", SQL(", ").join(scores))

    def _exact_score_one2many_sql(self, model, alias, path, sql_term):
        # exact boost through a one2many hop, e.g.
        # '=product_variant_ids.default_code' on product.template: boost
        # when any (active) child record's field equals the term
        rel_name, sub_name = path.split(".")
        rel_field = model._fields[rel_name]
        assert rel_field.type == "one2many" and rel_field.inverse_name, (
            f"SearchRank field {self}: exact source {path!r} must traverse"
            " a one2many with an inverse field"
        )
        comodel = model.env[rel_field.comodel_name]
        sub_field = comodel._fields[sub_name]
        assert sub_field.store and sub_field.column_type, (
            f"SearchRank field {self}: exact source {path!r} must end on a"
            " stored column"
        )
        unaccent = model.env.registry.unaccent
        where = SQL(
            "%s = %s AND LOWER(%s) = LOWER(%s)",
            SQL.identifier("__search_rank", rel_field.inverse_name),
            SQL.identifier(alias, "id"),
            unaccent(SQL.identifier("__search_rank", sub_name)),
            sql_term,
        )
        if comodel._active_name:
            # mirror the document compute, which reads active children only
            where = SQL(
                "%s AND %s",
                where,
                SQL.identifier("__search_rank", comodel._active_name),
            )
        return SQL(
            "EXISTS (SELECT 1 FROM %s AS %s WHERE %s)::int * 2.0",
            SQL.identifier(comodel._table),
            SQL.identifier("__search_rank"),
            where,
        )
