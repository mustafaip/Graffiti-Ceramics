{
    'name': 'Stock Return with Breakage',
    'version': '19.0.1.0.0',
    'summary': 'Return delivery items and book damage expense via journal entry',
    'description': """
        Adds a "Return with Breakage" button on Delivery (stock.picking) forms.
        - Creates a reverse stock move to reduce inventory
        - Posts a journal entry booking the cost to a configurable Damage expense account
        - Inventory and Expense journals are configurable under Inventory > Settings
    """,
    'author': 'Custom',
    'category': 'Inventory',
    'depends': ['stock', 'account', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
        'wizard/stock_return_breakage_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
