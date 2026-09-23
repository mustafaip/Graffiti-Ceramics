# -*- coding: utf-8 -*-
import json
import logging
import requests
from odoo import models, api
from odoo.exceptions import UserError

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
        """Low level HTTP call. Used for both the immediate real-time push
        and for cron retries of queued jobs.
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
            timeout=15,
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

    def _oc_push(self, operation, model_name, build_payload):
        """Call from create()/write() overrides.

        `build_payload` is a callable(record) -> dict of fields to send.
        On success, stores/updates the local->remote mapping.
        On failure (remote down, timeout, ...) the record is queued for
        retry instead of blocking the user's save.
        """
        Mapping = self.env['oc.connector.mapping'].sudo()
        Queue = self.env['oc.connector.queue'].sudo()
        for rec in self:
            payload = build_payload(rec)
            payload['_remote_id'] = Mapping.get_remote_id(model_name, rec.id) or False
            try:
                result = self._oc_send_raw(model_name, operation, json.dumps(payload), rec.id)
                if result.get('local_id'):
                    Mapping.set_mapping(model_name, rec.id, result['local_id'], direction='push')
            except Exception as e:  # noqa: BLE001
                _logger.warning("OC Connector: queuing %s#%s after send failure: %s",
                                 model_name, rec.id, e)
                Queue.create({
                    'model': model_name,
                    'res_id': rec.id,
                    'operation': operation,
                    'payload': json.dumps(payload),
                    'state': 'pending',
                    'last_error': str(e)[:2000],
                })

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
