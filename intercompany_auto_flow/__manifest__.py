# -*- coding: utf-8 -*-
{
    'name': 'Intercompany Auto Flow',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Automates intercompany sales and purchase orders with stock moves',
    'description': """
Intercompany Auto Flow
======================
When Company A sells a product it does not stock, this module:
  1. Searches sibling companies (B, C) for available stock
  2. Automatically creates a Purchase Order in A from the supplying company
  3. Automatically creates a Sales Order in the supplying company to A
  4. Triggers all intercompany stock moves (OUT from B → IN to A → OUT from A → IN to Customer)

Works for any number of companies sharing the same Odoo database.
    """,
    'author': 'Custom',
    'depends': [
        'stock',
        'purchase',
        'sale',
        'sale_stock',
        'purchase_stock',
        'account',
        'base_accounting_kit',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/intercompany_flow_data.xml',
        'views/res_company_views.xml',
        'views/intercompany_flow_log_views.xml',
        'views/sale_order_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
