{
    "name": "Product Alternate Names",
    "version": "20.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Sell a product under alternate names while keeping the original product",
    "description": """
Adds an "Alternate Products" tab on the product form where additional selling
names can be maintained. On sales order lines the salesperson can pick a
"Sold As" name; the line still points to the original product (stock, price,
taxes, invoicing are unchanged) but the description printed on the quotation,
order and invoice uses the alternate name. Products can also be found in the
product search by any of their alternate names.
    """,
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["product", "sale"],
    "data": [
        "security/ir.access.csv",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "views/report_saleorder_templates.xml",
    ],
    "installable": True,
    "application": False,
}
