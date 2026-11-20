from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Make sure every product has a regular-name entry, point existing lines
    without a name at it, and refresh the printed labels."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["product.template"].with_context(active_test=False).search(
        []
    )._sync_primary_alternate_name()
    cr.execute(
        """
        UPDATE sale_order_line sol
           SET alternate_name_id = alt.id
          FROM product_product pp
          JOIN product_alternate_name alt
            ON alt.product_tmpl_id = pp.product_tmpl_id AND alt.is_primary
         WHERE sol.product_id = pp.id
           AND sol.alternate_name_id IS NULL
        """
    )
