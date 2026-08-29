from odoo.fields import Domain


def search_ranked(model, term, domain=None, limit=None, offset=0, field=None):
    """search() ``model``, matched against ``term`` and ordered by relevance.

    ``field`` names the model's SearchRank field; it may be omitted when the
    model has exactly one. With a falsy/blank ``term`` this degrades to a
    plain search of ``domain`` in the model's default order.
    """
    from .fields import SearchRank  # noqa: PLC0415 - avoid import cycle

    term = (term or "").strip()
    base = Domain(domain) if domain is not None else Domain.TRUE
    if not term:
        return model.search(base, limit=limit, offset=offset)
    if field is None:
        candidates = [
            f.name for f in model._fields.values() if isinstance(f, SearchRank)
        ]
        if len(candidates) != 1:
            raise ValueError(
                f"{model._name} has {len(candidates)} SearchRank fields"
                f" ({candidates}); pass field= explicitly"
            )
        field = candidates[0]
    model = model.with_context(search_rank_term=term)
    return model.search(
        base & Domain(field, "ilike", term),
        limit=limit,
        offset=offset,
        order=f"{field}.rank desc, {model._order}",
    )
