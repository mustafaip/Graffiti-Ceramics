# -*- coding: utf-8 -*-
{
    'name': 'Invoice Watermark (Cash / Credit)',
    'version': '19.0.2.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Auto-stamp Cash or Credit watermark on customer invoice PDFs',
    'description': """
Invoice Watermark
=================
Automatically detects the payment method on customer invoices and stamps
the printed PDF with a diagonal CASH or CREDIT watermark.

Logic
-----
- All payments via Cash journal → CASH watermark (green)
- Any non-cash or mixed payment  → CREDIT watermark (blue)
- Unpaid invoice                 → No watermark (default)

The watermark field can be overridden manually at any time via the
PDF Watermark dropdown on the invoice form.
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
