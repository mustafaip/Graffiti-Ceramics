# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import models, api
from odoo.exceptions import UserError
from .connector_queue import MAX_RETRIES

_logger = logging.getLogger(__name__)



class OcConnectorMixin(models.AbstractModel):
    """Shared helpers for pushing records to the remote Odoo instance and
    receiving records pushed from it. Inherited by every model that needs
    to sync: res.partner, product.template, uom.uom, product.pricelist,
    sale.order.
    """
    _name = 'oc.connector.mixin'
    _description = 'OC Connector: shared push/receive helpers'

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------
    @api.model
    def _oc_settings(self):
        return self.env['oc.connector.settings'].sudo().get_singleton()

    @api.model
    def _oc_role(self):
        return self._oc_settings().role

    @api.model
    def _oc_remote_url(self):
        return (self._oc_settings().remote_url or '').rstrip('/')

    @api.model
    def _oc_api_key(self):
        return self._oc_settings().api_key

    # ------------------------------------------------------------------
    # Outbound: push a record to the remote instance
    # ------------------------------------------------------------------
    @api.model
    def _oc_send_raw(self, model, operation, payload_json, local_id):
        """Low level HTTP call, used by the queue worker and Test Connection.

        Timeouts are (connect, read): an unreachable server fails in 3s instead
        of hanging a worker for the whole read timeout.
        """
        url = self._oc_remote_url()
        api_key = self._oc_api_key()
        if not url or not api_key:
            raise UserError("OC Connector: remote URL / API key is not configured "
                             "(Settings > Connector Bridge).")
        resp = requests.post(
            f"{url}/oc_connector/receive",
            json={
                'api_key': api_key,
                'model': model,
                'operation': operation,
                'local_id': local_id,
                'data': json.loads(payload_json) if isinstance(payload_json, str) else payload_json,
            },
            timeout=(3, 30),
        )
        resp.raise_for_status()
        try:
            result = resp.json()
        except ValueError:
            raise UserError(
                f"Remote returned a non-JSON response (HTTP {resp.status_code}): {resp.text[:300]}")
        if not result.get('success'):
            raise UserError(f"Remote rejected the record: {result.get('error')}")
        return result

    @api.model
    def _oc_build_payload(self, rec, builder_name):
        """Builds the JSON payload for `rec` at SEND time (so the remote always
        gets the latest values, and several quick edits collapse into one push)."""
        payload = getattr(rec, builder_name)(rec)
        payload['_remote_id'] = self.env['oc.connector.mapping'].sudo().get_remote_id(rec._name, rec.id) or False
        return payload

    def _oc_push(self, operation, model_name, build_payload):
        """Call from create()/write() overrides.

        Does NO network I/O. It only records "this record needs pushing" in the
        queue table, inside the caller's own transaction (so a rollback also
        discards the job), and wakes the queue cron. The HTTP call happens in
        the background job, never inside the user's request - that is what
        previously caused gateway timeouts whenever the remote was slow or
        unreachable, or when many records were written at once.
        """
        ctx = self.env.context
        if ctx.get('install_mode') or ctx.get('oc_connector_sync'):
            return  # module install/update data loading, or applying inbound sync
        if not (self._oc_remote_url() and self._oc_api_key()):
            return  # not configured yet: nothing to push to
        Queue = self.env['oc.connector.queue'].sudo()
        builder_name = build_payload.__name__
        queued = False
        for rec in self:
            # One open job per record is enough: payload is built at send time.
            job = Queue.search([
                ('model', '=', model_name), ('res_id', '=', rec.id),
                ('operation', '!=', 'unlink'),
                ('state', 'in', ['pending', 'failed']), ('retries', '<', MAX_RETRIES),
            ], limit=1)
            if job:
                if job.state == 'failed':
                    job.state = 'pending'
            else:
                Queue.create({
                    'model': model_name,
                    'res_id': rec.id,
                    'operation': operation,
                    'payload_builder': builder_name,
                    'state': 'pending',
                })
            queued = True
        if queued:
            Queue._oc_wake_cron()

    # ------------------------------------------------------------------
    # Inbound: find-or-create a local record from a remote payload
    # ------------------------------------------------------------------
    @api.model
    def _oc_find_or_create(self, model_name, domain, values, remote_id):
        """Generic find-or-create used by the receiving handlers.

        1. Look up an existing mapping for this remote_id.
        2. Otherwise, look up by business-key `domain`.
        3. Otherwise create a new record.
        Always (re)writes `values` so updates flow through too.
        """
        Mapping = self.env['oc.connector.mapping'].sudo()
        Model = self.env[model_name].sudo()

        local_id = Mapping.get_local_id(model_name, remote_id)
        record = Model.browse(local_id) if local_id else Model.browse()

        if not record.exists() and domain:
            record = Model.search(domain, limit=1)

        if record.exists():
            record.write(values)
        else:
            record = Model.create(values)

        Mapping.set_mapping(model_name, record.id, remote_id, direction='pull')
        return record.id
