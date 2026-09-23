# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OcConnectorController(http.Controller):

    @http.route('/oc_connector/receive', type='json', auth='public', methods=['POST'], csrf=False)
    def receive(self, **kwargs):
        # Everything is wrapped in one try/except so that ANY failure - even one
        # that happens before we get to the actual handler (a broken settings
        # record, a DB error, etc.) - comes back as a clean, readable message
        # instead of an unhandled exception that produces a malformed response.
        try:
            params = request.jsonrequest if hasattr(request, 'jsonrequest') else kwargs

            api_key = params.get('api_key')
            expected = request.env['oc.connector.settings'].sudo().get_singleton().api_key
            if not expected or api_key != expected:
                return {'success': False, 'error': 'Invalid API key'}

            model = params.get('model')
            operation = params.get('operation')
            data = params.get('data') or {}
            local_id = params.get('local_id')

            handler_name = f"_oc_receive_{model.replace('.', '_')}"
            mixin = request.env['oc.connector.mixin'].sudo()
            handler = getattr(mixin, handler_name, None)
            if not handler:
                return {'success': False, 'error': f'No handler registered for model {model}'}

            local_res_id = handler(operation, data, local_id)
            return {'success': True, 'local_id': local_res_id}
        except Exception as e:  # noqa: BLE001
            _logger.exception("OC Connector: failed to process incoming request")
            return {'success': False, 'error': f'{type(e).__name__}: {e}'}
