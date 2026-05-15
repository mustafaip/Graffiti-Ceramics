# -*- coding: utf-8 -*-
{
    'name': 'SO Attachment Transfer to MO / Subcontracting',
    'version': '19.0.3.0.0',
    'category': 'Manufacturing',
    'summary': 'Design Docs smart button on SO, auto-transfer to MO on confirmation',
    'description': """
SO Attachment Transfer
======================
Adds a Design Docs smart button to Quotations and Sales Orders.

Workflow
--------
1. Open any Quotation or Sales Order
2. Click the Design Docs smart button (paperclip icon)
3. Upload design documents in the attachment list
4. Print the Quotation: attachments appear as extra pages in the PDF
5. Confirm the order: all design docs are auto-copied to linked MOs
6. Open the MO: Design Docs smart button shows the count
7. Click it to view transferred files; chatter shows transfer note
    """,
    'author': 'Custom Development',
    'depends': ['sale_management', 'mrp'],
    'data': [
        'views/sale_order_views.xml',
        'views/mrp_production_views.xml',
        'report/sale_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
