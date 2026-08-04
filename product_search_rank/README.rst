===================
product_search_rank
===================

Ranked substring + fuzzy product searching, built on ``base_search_rank``.

Adds a ``search_rank`` field to ``product.product`` and
``product.template`` covering internal reference, name, barcode and
variant attribute values, and exposes it in their search views as
"Product (Ranked by Relevance)". Whole-value internal reference matches
rank first.

Dropdown (``name_search``) ranking is opted in per view by the
``product_search_rank_sale`` / ``_purchase`` / ``_account`` modules.
