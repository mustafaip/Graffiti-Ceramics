def migrate(cr, version):
    """Remove the technical 'regular name' entries used by earlier versions.

    An empty "Sold As" now means the product's regular name, so these rows
    only duplicated names in the UI.
    """
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'product_alternate_name' AND column_name = 'is_primary'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        UPDATE sale_order_line SET alternate_name_id = NULL
         WHERE alternate_name_id IN (
               SELECT id FROM product_alternate_name WHERE is_primary)
        """
    )
    cr.execute("DELETE FROM product_alternate_name WHERE is_primary")
