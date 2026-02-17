from . import models


def _pre_init_hook(env):
    """Allow installing in databases with large amount of data, quickly"""
    env.cr.execute("""ALTER TABLE "stock_picking" ADD COLUMN "has_cpq_phantom" bool;""")
    env.cr.execute("""UPDATE stock_picking SET has_cpq_phantom = FALSE""")

    env.cr.execute(
        """ALTER TABLE "product_template" ADD COLUMN "cpq_dynamic_bom_count" int4;"""
    )
    env.cr.execute("""UPDATE product_template SET cpq_dynamic_bom_count = 0""")
