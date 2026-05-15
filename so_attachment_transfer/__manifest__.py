# -*- coding: utf-8 -*-
{
    'name': 'SO Attachment Transfer to MO / Subcontracting',
    'version': '19.0.2.0.0',
    'category': 'Manufacturing',
    'summary': 'Transfer SO attachments to MO and Subcontracting Orders automatically',
    'description': """
SO Attachment Transfer
======================
Attach design documents to a Sales Order/Quotation. On confirmation:

  1. Attachments appear as extra pages on the printed Quotation PDF
  2. All attachments are auto-copied to linked Manufacturing Orders
  3. A smart button on the MO shows the count and opens the docs
  4. A chatter note is posted on the MO listing transferred files
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
