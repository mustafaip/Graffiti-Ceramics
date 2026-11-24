from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Create the regular-name entry for every existing product."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["product.template"].with_context(active_test=False).search(
        []
    )._sync_primary_alternate_name()
