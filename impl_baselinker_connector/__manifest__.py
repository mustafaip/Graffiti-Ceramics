{
    'name': 'BaseLinker Connector',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Connect Odoo to BaseLinker - multichannel e-commerce integration with Shoptet, Allegro, Shopify, WooCommerce, Amazon, Heureka and 100+ more',
    'description': """
        Synchronize orders, products, and customers between BaseLinker and Odoo.

        BaseLinker connects to over 100 sales channels including Allegro, Amazon,
        eBay, Shopify, WooCommerce, Shoptet, Magento, PrestaShop, and many more.

        Use this module to seamlessly connect your Odoo instance to 100+ e-commerce
        platforms, marketplaces, and shipping carriers including:
        Shoptet, Upgates, Pohoda, Money S3, Allegro, Amazon, eBay, Shopify,
        WooCommerce, Magento, PrestaShop, Heureka, Mall.cz, Packeta / Zasilkovna.

        Need a direct connector without BaseLinker?
        Contact IMPLEMENTO - we build custom Odoo integrations for any platform!
    """,
    'author': 'IMPLEMENTO s.r.o.',
    'maintainer': 'IMPLEMENTO s.r.o.',
    'website': 'https://www.implemento.eu',
    'support': 'support@implemento.eu',
    'license': 'OPL-1',
    'price': 0,
    'currency': 'EUR',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/baselinker_backend_views.xml',
        'views/menu_views.xml',
        'data/ir_cron.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
