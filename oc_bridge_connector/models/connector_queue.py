# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

MAX_RETRIES = 8


class OcConnectorQueue(models.Model):
    """Outbound sync buffer. A record lands here whenever a real-time push
    fails (remote down, network blip, etc.) so it is not lost - a cron
    retries it every 5 minutes.
    """
    _name = 'oc.connector.queue'
    _description = 'OC Connector: outbound sync queue'
    _order = 'create_date desc'

    model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    operation = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('unlink', 'Delete'),
    ], required=True)
    payload = fields.Text(required=True, help="JSON payload that will be (re-)sent to the remote server")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('done', 'Done'),
    ], default='pending', required=True)
    retries = fields.Integer(default=0)
    last_error = fields.Text()

    def _cron_retry_failed(self):
        """Runs every 5 minutes: retries all pending/failed jobs under the retry cap."""
        jobs = self.search([('state', 'in', ['pending', 'failed']), ('retries', '<', MAX_RETRIES)])
        Mixin = self.env['oc.connector.mixin']
        for job in jobs:
            try:
                result = Mixin._oc_send_raw(job.model, job.operation, job.payload, job.res_id)
                if result.get('local_id'):
                    self.env['oc.connector.mapping'].sudo().set_mapping(
                        job.model, job.res_id, result['local_id'], direction='push')
                job.write({'state': 'done'})
            except Exception as e:  # noqa: BLE001
                job.write({
                    'state': 'failed',
                    'retries': job.retries + 1,
                    'last_error': str(e)[:2000],
                })
                _logger.warning("OC Connector retry failed for %s#%s: %s", job.model, job.res_id, e)
