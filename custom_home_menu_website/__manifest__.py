{
    'name': 'Premium Home Menu - Website - Community Edition',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Bridge module for Custom Home Menu and Website.',
    'description': """
        Glue module that automatically installs when both custom_home_menu and website are present.
        It enables the home menu button on the website frontend.
    """,
    'author': 'Rashid Habibullah',
    'depends': ['custom_home_menu', 'website'],
    'data': [],
    'assets': {
        'web.assets_frontend': [
            'custom_home_menu_website/static/src/js/website_custom_home_menu.js',
            'custom_home_menu/static/src/scss/custom_home_menu.scss',
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'images': ['static/description/screenshot_main.png'],
}
