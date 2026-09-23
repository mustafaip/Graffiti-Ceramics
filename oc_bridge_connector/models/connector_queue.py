# -*- coding: utf-8 -*-
import logging
from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MAX_RETRIES = 8


class OcConnectorQueue(models.Model):
    """Outbound sync buffer. A record lands here whenever a real-time push
    fails (remote down, network blip, etc.) so it is not lost - a cron
    retries it every 5 minutes, or you can force it immediately with the
    "Retry Now" button on the record.
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

    def _retry_one(self, job):
        """Shared by the cron and the manual button. Returns True on success."""
        Mixin = self.env['oc.connector.mixin']
        try:
            result = Mixin._oc_send_raw(job.model, job.operation, job.payload, job.res_id)
            if result.get('local_id'):
                self.env['oc.connector.mapping'].sudo().set_mapping(
                    job.model, job.res_id, result['local_id'], direction='push')
            job.write({'state': 'done', 'last_error': False})
            return True
        except Exception as e:  # noqa: BLE001
            job.write({
                'state': 'failed',
                'retries': job.retries + 1,
                'last_error': str(e)[:2000],
            })
            _logger.warning("OC Connector retry failed for %s#%s: %s", job.model, job.res_id, e)
            return False

    def _cron_retry_failed(self):
        """Runs every 5 minutes: retries all pending/failed jobs under the retry cap."""
        jobs = self.search([('state', 'in', ['pending', 'failed']), ('retries', '<', MAX_RETRIES)])
        for job in jobs:
            self._retry_one(job)

    def action_retry_now(self):
        """Manual "Retry Now" button - retries immediately and raises the
        exact error in the UI if it still fails, instead of waiting for the
        next cron tick and having to reopen the record to see the result."""
        for job in self:
            ok = self._retry_one(job)
            if not ok:
                raise UserError(f"Retry failed: {job.last_error}")
