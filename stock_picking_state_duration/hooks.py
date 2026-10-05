from odoo.tools.sql import column_exists, create_column


def pre_init_hook(env):
    """Backfill state_date so install doesn't stamp every picking with now.

    Creating the columns up front stops the ORM computing them. The last
    tracked state change is when the picking entered its current state;
    pickings with no tracked change fall back to create_date.
    """
    cr = env.cr
    if column_exists(cr, "stock_picking", "state_date"):
        return

    create_column(cr, "stock_picking", "state_date", "timestamp")
    create_column(cr, "stock_picking", "state_date_state", "varchar")
    cr.execute(
        """
        UPDATE stock_picking
           SET state_date = create_date,
               state_date_state = state
        """
    )
    cr.execute(
        """
        UPDATE stock_picking p
           SET state_date = last_change.date
          FROM (
                SELECT m.res_id, MAX(m.date) AS date
                  FROM mail_tracking_value v
                  JOIN mail_message m ON m.id = v.mail_message_id
                  JOIN ir_model_fields f ON f.id = v.field_id
                 WHERE m.model = 'stock.picking'
                   AND f.model = 'stock.picking'
                   AND f.name = 'state'
              GROUP BY m.res_id
               ) last_change
         WHERE last_change.res_id = p.id
        """
    )
