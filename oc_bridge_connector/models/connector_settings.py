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
    singleton_key = fields.Char(default='singleton', readonly=True)
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

    _sql_constraints = [
        ('uniq_singleton', 'unique(singleton_key)',
         'Only one Connector Bridge settings record may exist.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._oc_clean_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._oc_clean_vals(vals)
        return super().write(vals)

    @staticmethod
    def _oc_clean_vals(vals):
        """Guards against the #1 cause of "same key, still rejected": invisible
        whitespace/newlines picked up from copy-pasting."""
        if vals.get('api_key') is not None:
            vals['api_key'] = (vals['api_key'] or '').strip()
        if vals.get('remote_url') is not None:
            vals['remote_url'] = (vals['remote_url'] or '').strip().rstrip('/')

    @api.model
    def get_singleton(self):
        """Always returns the same one settings record, creating it on first use.
        Guarded against a race where two records get created concurrently on
        first-ever use - the unique constraint above makes the loser of that
        race fall back to re-reading the winner instead of ending up orphaned.
        """
        rec = self.search([], limit=1)
        if rec:
            return rec
        try:
            with self.env.cr.savepoint():
                return self.create({})
        except Exception:
            return self.search([], limit=1)

    def action_test_connection(self):
        """Pings the OTHER instance right now, using the current saved values,
        and reports back exactly what happened - no waiting for the retry cron,
        no touching real data.
        """
        self.ensure_one()
        Mixin = self.env['oc.connector.mixin']
        try:
            Mixin._oc_send_raw('ping', 'write', '{}', 0)
            message = "Success - the remote instance accepted the request and the API key matches."
            notif_type = 'success'
            sticky = False
        except Exception as e:  # noqa: BLE001
            message = f"Failed: {e}"
            notif_type = 'danger'
            sticky = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Connector Bridge - Test Connection',
                'message': message,
                'type': notif_type,
                'sticky': sticky,
            },
        }
