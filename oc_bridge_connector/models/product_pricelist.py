# -*- coding: utf-8 -*-
from odoo import models, api


class ProductPricelist(models.Model):
    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'oc.connector.mixin']

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
        if self._oc_role() != 'enterprise':
            return
        self._oc_push(operation, 'product.pricelist', self._oc_pricelist_payload)

    def _oc_pricelist_payload(self, rec):
        items = []
        for item in rec.item_ids:
            items.append({
                'applied_on': item.applied_on,
                'default_code': item.product_tmpl_id.default_code if item.product_tmpl_id else False,
                'compute_price': item.compute_price,
                'fixed_price': item.fixed_price,
                'percent_price': item.percent_price,
                'min_quantity': item.min_quantity,
            })
        return {
            'name': rec.name,
            'currency_name': rec.currency_id.name,
            'active': rec.active,
            'items': items,
            '_match_key': {'name': rec.name},
        }
