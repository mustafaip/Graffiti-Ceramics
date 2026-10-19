{
    'name': 'Sales: Quotations Only',
    'version': '20.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Hide the Confirm button so users can only create quotations',
    'description': """
Hides the "Confirm" button on sales orders for everyone except members of the
"Can Confirm Sales Orders" group, and blocks confirmation server-side as well.
    """,
    'depends': ['sale'],
    'data': [
        'security/security.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
