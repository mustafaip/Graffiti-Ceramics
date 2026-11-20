{
    "name": "Product Alternate Names",
<<<<<<< Updated upstream
    "version": "20.0.1.0.3",
=======
<<<<<<< HEAD
    "version": "20.0.1.1.0",
=======
    "version": "20.0.1.0.3",
>>>>>>> 8bc0e1585a15edd07cd7b435bc6242acd5679e60
>>>>>>> Stashed changes
    "category": "Sales/Sales",
    "summary": "Sell the same product under alternate names (aliases) on quotes, orders and invoices",
    "description": """
Product Alternate Names
=======================
Maintain additional selling names (and optional codes / sales descriptions) on
the product form, in the "Alternate Names" tab.

On a sales order line pick the name in the "Sold As" column. The line still
points to the original product, so stock, price, taxes and accounting are
untouched, but the line title printed on the quotation, order confirmation and
customer invoice uses the alternate name.

Products can also be found in any product search by their alternate names or
codes.
    """,
    "author": "AMP Data Solutions",
    "license": "LGPL-3",
    "depends": ["product", "sale", "account"],
    "data": [
        "security/ir.access.csv",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
    ],
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": False,
}
