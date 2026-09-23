# -*- coding: utf-8 -*-
from odoo import models, fields, api


class OcConnectorSettings(models.Model):
    """Plain settings record - deliberately NOT built on res.config.settings.
    That wizard needs specific JS wiring to behave (js_class="base_settings")
    and falls back to a confusing generic record UI without it. A normal
    model with a normal Save button is far more predictable.
    """
    _name = 'oc.connector.settings'
    _description = 'OC Connector: bridge settings (singleton)'

    name = fields.Char(default='Connector Bridge Settings', readonly=True)
    role = fields.Selection([
        ('enterprise', 'Enterprise (master data source)'),
        ('community', 'Community (sales source)'),
    ], required=True, default='community', string='This instance is')
    remote_url = fields.Char(
        string='Remote Odoo URL',
        help="Base URL of the OTHER instance, e.g. https://enterprise.mycompany.com (no trailing slash).")
    api_key = fields.Char(
        string='Shared API Key',
        help="Any long random string. Must be identical on both instances.")

    @api.model
    def get_singleton(self):
        """Always returns the same one settings record, creating it on first use."""
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({})
        return rec
