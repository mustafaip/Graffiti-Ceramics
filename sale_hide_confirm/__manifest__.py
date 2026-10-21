{
    'name': 'Sales: Quotations Only',
    'version': '20.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Hide the Confirm button for everyone so only quotations can be created',
    'description': """
Removes the "Confirm" button from sales orders for all users (including
administrators) and blocks direct confirmation server-side.
    """,
    'depends': ['sale'],
    'data': [],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
