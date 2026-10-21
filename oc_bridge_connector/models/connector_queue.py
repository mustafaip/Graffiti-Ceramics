# -*- coding: utf-8 -*-
import json
import logging
import time
from datetime import timedelta

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MAX_RETRIES = 8
RETRY_DELAY_MINUTES = 5      # a failed job is retried after this long
BATCH_LIMIT = 200            # max jobs per cron run
TIME_BUDGET_SECONDS = 45     # stop early and re-trigger rather than hit the cron time limit
CRON_XMLID = 'oc_bridge_connector.ir_cron_oc_connector_retry'


class OcConnectorQueue(models.Model):
    """Outbound sync queue. Every create/write on a synced record adds (or
    refreshes) one row here inside the user's own transaction; a background
    cron sends them to the remote Odoo. The user's save therefore never waits
    on the network. Failed jobs are retried automatically (see constants above),
    or immediately with the "Retry Now" button.
    """
    _name = 'oc.connector.queue'
    _description = 'OC Connector: outbound sync queue'
    _order = 'id'

    model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    operation = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('unlink', 'Delete'),
    ], required=True)
    payload_builder = fields.Char(
        help="Name of the method that builds the payload at send time. Empty for "
             "jobs that carry a ready-made payload (older jobs and deletions).")
    payload = fields.Text(help="Ready-made JSON payload. When empty it is built from the live "
                               "record when the job is sent.")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('done', 'Done'),
    ], default='pending', required=True, index=True)
    retries = fields.Integer(default=0)
    last_error = fields.Text()

    # ------------------------------------------------------------------
    def _oc_wake_cron(self):
        """Ask the cron to run as soon as possible (does not block)."""
        cron = self.env.ref(CRON_XMLID, raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()

    def _oc_job_payload(self, job):
        """Returns the JSON string to send, or None if the record no longer exists."""
        if job.payload:
            return job.payload
        rec = self.env[job.model].sudo().browse(job.res_id)
        if not rec.exists():
            return None
        payload = self.env['oc.connector.mixin']._oc_build_payload(rec, job.payload_builder)
        return json.dumps(payload)

    def _retry_one(self, job):
        """Shared by the cron and the manual button. Returns True on success."""
        Mixin = self.env['oc.connector.mixin']
        try:
            payload = self._oc_job_payload(job)
            if payload is None:
                job.write({'state': 'done', 'last_error': 'Record no longer exists - nothing to send.'})
                return True
            result = Mixin._oc_send_raw(job.model, job.operation, payload, job.res_id)
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
            _logger.warning("OC Connector send failed for %s#%s: %s", job.model, job.res_id, e)
            return False

    def _cron_retry_failed(self):
        """Background worker (name kept for upgrade compatibility). Sends all
        pending jobs, plus failed ones that are due for a retry. Commits after
        every job so progress survives a crash, and stops after a time budget,
        re-triggering itself if work remains."""
        started = time.monotonic()
        due = fields.Datetime.now() - timedelta(minutes=RETRY_DELAY_MINUTES)
        jobs = self.search([
            '|', ('state', '=', 'pending'),
            '&', '&', ('state', '=', 'failed'), ('retries', '<', MAX_RETRIES), ('write_date', '<=', due),
        ], limit=BATCH_LIMIT, order='id')
        for job in jobs:
            if time.monotonic() - started > TIME_BUDGET_SECONDS:
                self._oc_wake_cron()
                break
            self._retry_one(job)
            self._oc_commit()

    def _oc_commit(self):
        if not getattr(self.env.registry, 'in_test_mode', lambda: False)():
            self.env.cr.commit()

    def action_retry_now(self):
        """Manual "Retry Now" button - sends immediately and raises the exact
        error in the UI if it still fails."""
        for job in self:
            ok = self._retry_one(job)
            if not ok:
                raise UserError(f"Retry failed: {job.last_error}")
