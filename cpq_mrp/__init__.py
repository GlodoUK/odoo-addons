from . import models


def _pre_init_hook(cr):
    """Allow installing in databases with large amount of data, quickly"""
    cr.execute("""ALTER TABLE "stock_picking" ADD COLUMN "has_cpq_phantom" bool;""")
    cr.execute("""UPDATE stock_picking SET has_cpq_phantom = FALSE""")

    cr.execute(
        """ALTER TABLE "product_template" ADD COLUMN "cpq_dynamic_bom_count" int4;"""
    )
    cr.execute("""UPDATE product_template SET cpq_dynamic_bom_count = 0""")
