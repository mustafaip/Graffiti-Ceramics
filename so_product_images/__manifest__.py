# -*- coding: utf-8 -*-
{
    'name': 'Quotation Product Images & Design',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Show product image and design per line in quotation PDF',
    'author': 'Custom Development',
    'depends': ['sale_management'],
    'data': [
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'report/sale_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
