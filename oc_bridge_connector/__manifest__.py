# -*- coding: utf-8 -*-
{
    'name': 'Community-Enterprise Bridge Connector',
    'version': '17.0.1.0.0',
    'category': 'Sales/Connector',
    'summary': 'Syncs master data (Products, UoM, Customers, Pricelists) from Enterprise '
               'to Community, and Quotations/Sales Orders from Community to Enterprise.',
    'description': """
Odoo Community <-> Enterprise Bridge Connector
================================================
Install this SAME module on BOTH databases, then configure the role under
Settings > Connector Bridge:

Enterprise database  -> role = "Enterprise (master data source)"
    - Pushes Products, UoM, Customers and Pricelists to Community whenever
      those records are created or updated.
    - Receives Quotations / Sales Orders pushed from Community.

Community database    -> role = "Community (sales source)"
    - Receives master data pushed from Enterprise (creates/updates records
      locally, matched by business key so nothing is duplicated).
    - Pushes Quotations / Sales Orders to Enterprise whenever they are
      created or updated.

Sync is real-time (push on write, over an authenticated HTTP/JSON endpoint).
If the remote server is unreachable when a push is attempted, the change is
queued and retried automatically every 5 minutes - see Connector Bridge >
Sync Queue to monitor / debug failures.
""",
    'author': 'Custom Build',
    'depends': ['base', 'sale_management', 'product', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/connector_config_views.xml',
        'views/connector_queue_views.xml',
        'views/connector_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
