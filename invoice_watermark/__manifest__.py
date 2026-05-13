# -*- coding: utf-8 -*-
{
    'name': 'Invoice Watermark (Cash / Credit)',
    'version': '19.0.3.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Auto-stamp Cash or Credit watermark on customer invoice PDFs',
    'description': """
Invoice Watermark
=================
Automatically detects the payment method on customer invoices and stamps
the printed PDF with a diagonal CASH or CREDIT watermark.

Detection Logic
---------------
  Cash journal (any payment method)  -> CASH watermark (green)
  Bank journal + Manual Payment      -> CASH watermark (green)
  Bank journal + Credit/PDC          -> CREDIT watermark (blue)
  Mixed payments (any Credit/PDC)    -> CREDIT watermark (blue)
  Unpaid invoice                     -> No watermark (default)

The PDF Watermark field can always be overridden manually on the invoice form.
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
