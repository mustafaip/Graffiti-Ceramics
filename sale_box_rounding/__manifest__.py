# -*- coding: utf-8 -*-
{
    'name': 'Sale Box Rounding (SQM / Pieces / Boxes)',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sell in SQM, round the quantity up to whole boxes, show Pieces and Boxes columns.',
    'description': """
Sale Box Rounding
=================
Products carry two conversion factors:

* **SQM per Piece**   - area of one piece (e.g. 0.72)
* **Pieces per Box**  - number of pieces in one box (e.g. 2)

The sales unit of measure stays SQM. On every Quotation / Sales Order line
the quantity is rounded UP to a whole number of boxes, and two extra columns
(Pieces, Boxes) are shown:

    SQM per Box = SQM per Piece x Pieces per Box      (0.72 x 2 = 1.44)
    Boxes       = ceil(Qty SQM / SQM per Box)         (50 / 1.44 = 34.72 -> 35)
    Pieces      = Boxes x Pieces per Box              (35 x 2 = 70)
    Qty SQM     = Boxes x SQM per Box                 (35 x 1.44 = 50.40)

Typing Boxes or Pieces instead of SQM works too (Pieces are rounded up to
whole boxes). Products without both factors, and lines not in the product's
own unit of measure, are left completely untouched.
""",
    'author': 'amp Data Solutions',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'views/product_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
