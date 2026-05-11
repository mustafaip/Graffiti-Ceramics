# -*- coding: utf-8 -*-
{
    'name': 'Invoice Watermark (Cash / Credit)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Add a Cash or Credit watermark to customer invoice PDFs',
    'description': """
Invoice Watermark
=================
Adds a dropdown field on customer invoices allowing the user to stamp the
printed PDF with a diagonal "CASH" or "CREDIT" watermark.

Features
--------
* Selection field on the invoice form (visible on customer invoices only)
* Watermark rendered via inline CSS in the QWeb PDF report
* Zero external dependencies — works with wkhtmltopdf out of the box
* Compatible with Odoo 19 Community Edition
    """,
    'author': 'Custom Development',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
        'report/invoice_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
