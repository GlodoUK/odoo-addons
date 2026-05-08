from odoo import http
from odoo.http import request


class CategorySearchController(http.Controller):
    @http.route(
        "/website_category_heirarchy_search/categories",
        type="jsonrpc",
        auth="public",
        website=True,
        readonly=True,
    )
    def get_categories(self, root_category_name="Vehicles", **kwargs):
        """Return a recursive category tree starting at *root_category_name*.

        Only categories with ``show_in_search_widget = True`` are included.

        Returns::

            {
                "depth": <int>,
                "children": [{"id": <int>, "name": <str>, "children": [...]}, ...]
            }
        """
        Category = request.env["product.public.category"].sudo()

        website_domain = [
            "|",
            ("website_id", "=", False),
            ("website_id", "=", request.website.id),
        ]
        visible_domain = website_domain + [("show_in_search_widget", "=", True)]

        root = Category.search(
            website_domain
            + [
                ("name", "=ilike", root_category_name),
                ("parent_id", "=", False),
            ],
            limit=1,
        )

        if not root:
            return {"depth": 0, "children": []}

        children = self._get_children(root, visible_domain)
        return {"depth": self._max_depth(children), "children": children}

    @http.route(
        "/website_category_heirarchy_search/counts",
        type="jsonrpc",
        auth="public",
        website=True,
        readonly=True,
    )
    def get_counts(self, category_ids, **kwargs):
        """Return published product counts for a batch of category IDs.

        Uses ``sale_product_domain()`` so counts always match the shop listing.
        Returns ``{"<id>": <count>, ...}``.
        """
        base_domain = request.website.sale_product_domain()
        Product = request.env["product.template"].sudo()
        return {
            str(cat_id): Product.search_count(
                base_domain + [("public_categ_ids", "child_of", int(cat_id))]
            )
            for cat_id in category_ids
        }

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_children(self, category, domain):
        items = []
        for child in category.child_id.filtered_domain(domain):
            grandchildren = self._get_children(child, domain)
            items.append(
                {"id": child.id, "name": child.name, "children": grandchildren}
            )
        is_leaf_level = not any(item["children"] for item in items)
        items.sort(key=lambda x: x["name"], reverse=is_leaf_level)
        return items

    def _max_depth(self, nodes):
        if not nodes:
            return 0
        return 1 + max(self._max_depth(n["children"]) for n in nodes)
