from . import models


def _post_init_hook(env):
    """Create the regular-name entry for every existing product."""
    env["product.template"].with_context(active_test=False).search(
        []
    )._sync_primary_alternate_name()
