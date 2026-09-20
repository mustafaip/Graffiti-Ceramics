# -*- coding: utf-8 -*-
from odoo import models, api


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'oc.connector.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._oc_maybe_push('create')
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('oc_connector_sync'):
            self._oc_maybe_push('write')
        return res

    def _oc_maybe_push(self, operation):
        if self._oc_role() != 'community':
            return  # Community is the source of quotations/orders
        self._oc_push(operation, 'sale.order', self._oc_order_payload)

    def _oc_order_payload(self, rec):
        lines = []
        for line in rec.order_line:
            if line.display_type:
                continue
            lines.append({
                'default_code': line.product_id.default_code,
                'name': line.name,
                'product_uom_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
            })
        return {
            'source_reference': rec.name,  # e.g. "S00001" from Community
            'partner_match': {
                'vat': rec.partner_id.vat,
                'email': rec.partner_id.email,
                'name': rec.partner_id.name,
            },
            'date_order': rec.date_order and rec.date_order.isoformat(),
            'client_order_ref': rec.client_order_ref,
            'note': rec.note,
            'state': rec.state,
            'lines': lines,
            '_match_key': {'source_reference': rec.name},
        }
