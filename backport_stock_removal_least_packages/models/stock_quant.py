import heapq
import logging
from collections import namedtuple

from odoo import api, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        # XXX: This is a fudge, its not actually considered when reserving stock
        if removal_strategy == "least_packages":
            return "in_date ASC, id"
        return super()._get_removal_strategy_order(removal_strategy)

    @api.model
    def _update_reserved_quantity(
        self,
        product_id,
        location_id,
        quantity,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        self = self.sudo()
        backport_stock_removal_least_packages = False
        removal_strategy = self._get_removal_strategy(product_id, location_id)
        if removal_strategy == "least_packages":
            backport_stock_removal_least_packages = quantity

        return super(
            StockQuant,
            self.with_context(
                backport_stock_removal_least_packages=backport_stock_removal_least_packages
            ),
        )._update_reserved_quantity(
            product_id,
            location_id,
            quantity,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    def _gather(
        self,
        product_id,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
    ):
        removal_strategy = self._get_removal_strategy(product_id, location_id)
        if removal_strategy == "least_packages" and isinstance(
            self.env.context.get("backport_stock_removal_least_packages"), float
        ):
            domain = [("product_id", "=", product_id.id)]
            if not strict:
                if lot_id:
                    domain = expression.AND(
                        [
                            ["|", ("lot_id", "=", lot_id.id), ("lot_id", "=", False)],
                            domain,
                        ]
                    )
                if package_id:
                    domain = expression.AND(
                        [[("package_id", "=", package_id.id)], domain]
                    )
                if owner_id:
                    domain = expression.AND([[("owner_id", "=", owner_id.id)], domain])
                domain = expression.AND(
                    [[("location_id", "child_of", location_id.id)], domain]
                )
            else:
                domain = expression.AND(
                    [
                        ["|", ("lot_id", "=", lot_id.id), ("lot_id", "=", False)]
                        if lot_id
                        else [("lot_id", "=", False)],
                        domain,
                    ]
                )
                domain = expression.AND(
                    [
                        [("package_id", "=", package_id and package_id.id or False)],
                        domain,
                    ]
                )
                domain = expression.AND(
                    [[("owner_id", "=", owner_id and owner_id.id or False)], domain]
                )
                domain = expression.AND(
                    [[("location_id", "=", location_id.id)], domain]
                )

            qty = self.env.context.get("backport_stock_removal_least_packages")
            domain, order = (
                self._backport_run_least_packages_removal_strategy_astar(domain, qty),
                "in_date ASC, id",
            )
            return self.search(domain, order=order)

        return super()._gather(
            product_id,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    def _backport_run_least_packages_removal_strategy_astar(self, domain, qty):  # noqa: C901
        # Fetch the available packages and contents
        query = self._where_calc(domain)
        query_str, params = query.select(
            "package_id", "SUM(quantity - reserved_quantity) AS available_qty"
        )
        query_str += " GROUP BY package_id HAVING SUM(quantity - reserved_quantity) > 0 ORDER BY available_qty DESC"  # noqa: E501
        self._cr.execute(query_str, params)
        qty_by_package = self._cr.fetchall()

        # Items that do not belong to a package are added individually to the list, any
        # empty packages get removed.
        pkg_found = False
        new_qty_by_package = []
        none_elements = []

        for elem in qty_by_package:
            if elem[0] is None:
                none_elements.extend([(None, 1) for _ in range(int(elem[1]))])
            elif elem[1] != 0:
                new_qty_by_package.append(elem)
                pkg_found = True

        new_qty_by_package.extend(none_elements)
        qty_by_package = new_qty_by_package

        if not pkg_found:
            return domain
        size = len(qty_by_package)

        class PriorityQueue:
            def __init__(self):
                self.elements = []

            def empty(self) -> bool:
                return not self.elements

            def put(self, item, priority):
                heapq.heappush(self.elements, (priority, item))

            def get(self):
                return heapq.heappop(self.elements)[1]

        def heuristic(node):
            if node.next_index < size:
                return (
                    len(node.taken_packages)
                    + node.count_remaining / qty_by_package[node.next_index][1]
                )
            return len(node.taken_packages)

        def generate_domain(node):
            selected_single_items = []
            single_item_ids = False
            for pkg in node.taken_packages:
                if pkg[0] is None:
                    # Lazily retrieve ids for single items
                    if not single_item_ids:
                        single_item_ids = self.search(
                            expression.AND([[("package_id", "=", None)], domain])
                        ).mapped("id")
                    selected_single_items.append(single_item_ids.pop())

            expr = [
                (
                    "package_id",
                    "in",
                    [elem[0] for elem in node.taken_packages if elem[0] is not None],
                )
            ]
            if selected_single_items:
                expr = expression.OR([expr, [("id", "in", selected_single_items)]])
            return expression.AND([expr, domain])

        Node = namedtuple("Node", "count_remaining taken_packages next_index")

        frontier = PriorityQueue()
        frontier.put(Node(qty, (), 0), 0)

        best_leaf = Node(qty, (), 0)

        try:
            while not frontier.empty():
                current = frontier.get()

                if current.count_remaining <= 0:
                    return generate_domain(current)

                # Keep track of processed package amounts to only generate one branch
                # for the same amount
                last_count = None
                i = current.next_index
                while i < size:
                    pkg = qty_by_package[i]
                    i += 1
                    if pkg[1] == last_count:
                        continue
                    last_count = pkg[1]

                    count = current.count_remaining - pkg[1]
                    taken = current.taken_packages + (pkg,)
                    node = Node(count, taken, i)

                    if count < 0:
                        # Overselect case
                        if (
                            best_leaf.count_remaining > 0
                            or len(node.taken_packages) < len(best_leaf.taken_packages)
                            or (
                                len(node.taken_packages)
                                == len(best_leaf.taken_packages)
                                and node.count_remaining > best_leaf.count_remaining
                            )
                        ):
                            best_leaf = node
                        continue

                    if i >= size and count != 0:
                        # Not enough packages case
                        if node.count_remaining < best_leaf.count_remaining:
                            best_leaf = node
                        continue

                    frontier.put(node, heuristic(node))
        except MemoryError:
            _logger.info(
                "Ran out of memory while trying to use the least_packages strategy to"
                " get quants. Domain: %s",
                domain,
            )
            return domain

        # no exact matching possible, use best leaf
        return generate_domain(best_leaf)
