# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OcConnectorController(http.Controller):

    @http.route('/oc_connector/receive', type='http', auth='public', methods=['POST'], csrf=False)
    def receive(self, **kwargs):
        # type='http' (not 'json') is deliberate: it gives us full control over
        # the exact request/response body instead of requiring Odoo's internal
        # JSON-RPC 2.0 envelope, which our own client does not send.
        try:
            raw = request.httprequest.get_data()
            params = json.loads(raw) if raw else {}

            api_key = params.get('api_key')
            expected = request.env['oc.connector.settings'].sudo().get_singleton().api_key
            if not expected or api_key != expected:
                return self._json_response({'success': False, 'error': 'Invalid API key'})

            model = params.get('model')
            operation = params.get('operation')
            data = params.get('data') or {}
            local_id = params.get('local_id')

            handler_name = f"_oc_receive_{model.replace('.', '_')}"
            mixin = request.env['oc.connector.mixin'].sudo()
            handler = getattr(mixin, handler_name, None)
            if not handler:
                return self._json_response(
                    {'success': False, 'error': f'No handler registered for model {model}'})

            local_res_id = handler(operation, data, local_id)
            return self._json_response({'success': True, 'local_id': local_res_id})
        except Exception as e:  # noqa: BLE001
            _logger.exception("OC Connector: failed to process incoming request")
            return self._json_response({'success': False, 'error': f'{type(e).__name__}: {e}'})

    @staticmethod
    def _json_response(payload):
        if hasattr(request, 'make_json_response'):
            return request.make_json_response(payload)
        # Fallback for Odoo versions without the make_json_response helper.
        return request.make_response(
            json.dumps(payload),
            headers=[('Content-Type', 'application/json')],
        )
