{
    "name": "Web Responsive | Enterprise Theme",
    'summary': 'Modern Responsive Backend Theme with Enterprise Home Menu, Mobile Burger Drawer & Dark Mode Support',
    'category': 'Technical',
    'version': '20.0.1.0.0',
    'author': 'Micra Digital',
    'maintainer': 'Micra Digital',
    'website': 'https://micra.digital',
    'depends': ['web', 'base_setup'],
    'auto_install': ['web'],
    'data': [
        'views/webclient_templates.xml',
        'views/res_config_settings.xml',
        'views/res_users_views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('after', 'web/static/src/scss/primary_variables.scss', 'micra_web_theme/static/src/**/*.variables.scss'),
            ('before', 'web/static/src/scss/primary_variables.scss', 'micra_web_theme/static/src/scss/primary_variables.scss'),
        ],
        'web._assets_secondary_variables': [
            ('before', 'web/static/src/scss/secondary_variables.scss', 'micra_web_theme/static/src/scss/secondary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('before', 'web/static/src/scss/bootstrap_overridden.scss', 'micra_web_theme/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web.assets_frontend': [
            'micra_web_theme/static/src/webclient/home_menu/home_menu_background.scss', # used by login page
            'micra_web_theme/static/src/webclient/navbar/navbar.scss',
        ],
        'web.assets_backend': [
            'micra_web_theme/static/src/webclient/**/*.scss',
            'micra_web_theme/static/src/views/**/*.scss',

            'micra_web_theme/static/src/core/**/*',
            'micra_web_theme/static/src/webclient/**/*.js',
            ('after', 'web/static/src/views/list/list_renderer.xml', 'micra_web_theme/static/src/views/list/list_renderer_desktop.xml'),
            ('after', 'web/static/src/views/kanban/kanban_renderer.xml', 'micra_web_theme/static/src/views/kanban/kanban_renderer.xml'),
            ('after', 'web/static/src/views/kanban/kanban_header.xml', 'micra_web_theme/static/src/views/kanban/kanban_header.xml'),
            ('after', 'web/static/src/views/widgets/ribbon/ribbon.xml', 'micra_web_theme/static/src/views/widgets/ribbon/ribbon.xml'),
            ('after', 'web/static/src/views/calendar/calendar_controller.xml', 'micra_web_theme/static/src/views/calendar/calendar_controller.xml'),
            ('after', 'web/static/src/views/calendar/calendar_side_panel/calendar_side_panel.xml', 'micra_web_theme/static/src/views/calendar/calendar_side_panel/calendar_side_panel.xml'),
            'micra_web_theme/static/src/webclient/**/*.xml',
            'micra_web_theme/static/src/views/**/*.js',
            'micra_web_theme/static/src/views/**/*.xml',
            'micra_web_theme/static/src/search/**/*.js',
            'micra_web_theme/static/src/search/**/*.scss',
            ('after', '/web/static/src/search/control_panel/control_panel.xml', 'micra_web_theme/static/src/search/control_panel/control_panel.xml'),
            ('remove', 'micra_web_theme/static/src/views/pivot/**'),
            ('remove', 'micra_web_theme/static/src/views/graph/**'),
            ('remove', 'micra_web_theme/static/src/**/*.dark.scss'),
        ],
        'web.assets_backend_lazy': [
            'micra_web_theme/static/src/views/pivot/**',
            'micra_web_theme/static/src/views/graph/**',
        ],
        'web.assets_backend_lazy_dark': [
            ('include', 'web.dark_mode_variables'),
            ('before', 'micra_web_theme/static/src/scss/bootstrap_overridden.scss', 'micra_web_theme/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'micra_web_theme/static/src/scss/bs_functions_overridden.dark.scss'),
        ],
        'web.assets_web': [
            ('replace', 'web/static/src/main.js', 'micra_web_theme/static/src/main.js'),
        ],
        "web.dark_mode_variables": [
            ('before', 'micra_web_theme/static/src/scss/primary_variables.scss', 'micra_web_theme/static/src/scss/primary_variables.dark.scss'),
            ('before', 'micra_web_theme/static/src/**/*.variables.scss', 'micra_web_theme/static/src/**/*.variables.dark.scss'),
            ('before', 'micra_web_theme/static/src/scss/secondary_variables.scss', 'micra_web_theme/static/src/scss/secondary_variables.dark.scss'),
        ],
        "web.assets_web_dark": [
            ('include', 'web.dark_mode_variables'),
            ('before', 'micra_web_theme/static/src/scss/bootstrap_overridden.scss', 'micra_web_theme/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'micra_web_theme/static/src/scss/bs_functions_overridden.dark.scss'),
            'micra_web_theme/static/src/**/*.dark.scss',
        ],
    },
    "images": ["static/description/banner.png"],
    'license': 'OPL-1',
}
