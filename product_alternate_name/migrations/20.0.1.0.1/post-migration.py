def migrate(cr, version):
    """Intentionally empty.

    Replaces an obsolete post-migration from an earlier version that called
    product.template._sync_primary_alternate_name(), which no longer exists.
    All work for 20.0.1.1.0 is done in pre-migration.py.
    """
    return
