from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Move to the Odoo 20 line layout.

    * make sure every product has its regular-name entry;
    * older versions stored the alias as the first line of the line
      description (``name``). The title now lives in ``label`` and is built
      from the alias, so strip that legacy first line to avoid printing the
      alias twice.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["product.template"].with_context(active_test=False).search(
        []
    )._sync_primary_alternate_name()

    lines = env["sale.order.line"].with_context(active_test=False).search(
        [("alternate_name_id", "!=", False)]
    )
    for line in lines:
        alt = line.alternate_name_id
        if alt.is_primary or not line.name:
            continue
        code = alt.code or line.product_id.default_code
        legacy_first_line = "[%s] %s" % (code, alt.name) if code else alt.name
        parts = line.name.split("\n")
        if parts[0] == legacy_first_line:
            cr.execute(
                "UPDATE sale_order_line SET name = %s WHERE id = %s",
                ("\n".join(parts[1:]), line.id),
            )
    env.invalidate_all()
