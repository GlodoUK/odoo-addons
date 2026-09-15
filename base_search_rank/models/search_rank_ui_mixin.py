from odoo import api, models
from odoo.fields import Domain

from ..fields import SearchRank
from ..utils import search_ranked


class SearchRankUiMixin(models.AbstractModel):
    """Opt-in UI wiring for models declaring a SearchRank field.

    - ``name_search`` returns ranked + fuzzy suggestions when the caller
      opts in via context — per m2o field, per view::

          <field name="product_id" context="{'search_rank_enable': True}"/>

      Everything else (including programmatic callers using name_search as
      a conservative matcher, where fuzzy must not turn "not found" into a
      plausible wrong record) stays stock. Assumes a single SearchRank
      field on the model; override to disambiguate if there are several.

    - ``_search`` orders by relevance whenever the domain contains a
      condition on a SearchRank field (a search-view facet on it, or any
      programmatic domain); other searches are untouched. Rank must lead
      even over an explicit order — view archs hard-code default_order,
      which the client sends indistinguishably from a user's column sort —
      so the caller's order becomes the tiebreak within equal ranks.
    """

    _name = "base_search_rank.mixin"
    _description = "Ranked Search UI Wiring"

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        if (
            name
            and operator in ("ilike", "like", "=ilike", "=like")
            and self.env.context.get("search_rank_enable")
        ):
            records = search_ranked(self, name, domain=domain, limit=limit)
            return [(record.id, record.display_name) for record in records.sudo()]
        return super().name_search(
            name=name, domain=domain, operator=operator, limit=limit
        )

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        condition = next(
            (
                condition
                for condition in Domain(domain).iter_conditions()
                if isinstance(self._fields.get(condition.field_expr), SearchRank)
                and condition.operator in ("ilike", "like", "=ilike", "=like", "=")
                and isinstance(condition.value, str)
                and condition.value.strip()
            ),
            None,
        )
        if condition:
            self = self.with_context(search_rank_term=condition.value.strip())
            order = f"{condition.field_expr}.rank desc, {order or self._order}"
        return super()._search(
            domain, offset=offset, limit=limit, order=order, **kwargs
        )
