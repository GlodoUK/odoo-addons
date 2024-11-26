from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Ensure that the cpq_custom_combination_indices is deterministic (i.e. not a random
    # order)
    variant_ids = (
        env["product.product"]
        .with_context(active_test=False)
        .search([("cpq_custom_combination_indices", "!=", False)])
    )
    for variant_id in variant_ids:
        valid = ",".join(sorted(variant_id.cpq_custom_combination_indices.split(",")))
        if valid != variant_id.cpq_custom_combination_indices:
            variant_id.cpq_custom_combination_indices = valid
