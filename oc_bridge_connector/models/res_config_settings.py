# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    oc_connector_role = fields.Selection([
        ('enterprise', 'Enterprise (master data source)'),
        ('community', 'Community (sales source)'),
    ], string='This instance is', config_parameter='oc_connector.role', default='community')
    oc_connector_remote_url = fields.Char(
        string='Remote Odoo URL', config_parameter='oc_connector.remote_url',
        help="Base URL of the OTHER Odoo instance, e.g. https://enterprise.mycompany.com "
             "(no trailing slash).")
    oc_connector_api_key = fields.Char(
        string='Shared API Key', config_parameter='oc_connector.api_key',
        help="Any long random string. Must be set to the EXACT same value on both instances.")
