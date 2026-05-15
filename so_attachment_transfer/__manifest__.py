# -*- coding: utf-8 -*-
{
    'name': 'SO Attachment Transfer to MO / Subcontracting',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Transfer SO attachments to MO and Subcontracting Orders automatically',
    'description': """
SO Attachment Transfer
======================
When a Sales Order is confirmed, all attachments are automatically copied to:
  - Linked Manufacturing Orders (MO)
  - Linked Subcontracting Orders

Features
--------
* All SO attachments append as extra pages on the printed Quotation PDF
* On SO confirmation, attachments are copied to MO and Subcontracting Orders
* Smart button on MO/Subcontracting shows count of transferred design docs
* Chatter message posted on MO/Subcontracting confirming the transfer
* Transferred attachments tagged with is_so_design_doc for easy filtering
    """,
    'author': 'Custom Development',
    'depends': ['sale_management', 'mrp'],
    'data': [
        'views/mrp_production_views.xml',
        'report/sale_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
