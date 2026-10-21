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
                'default_code': item.product_tmpl_id.default_code if item.product_tmpl_id else False,
                # Odoo 20: compute_price is fixed / discount / markup and the
                # percentage lives in price_discount (percent_price is gone).
                'compute_price': item.compute_price,
                'fixed_price': item.fixed_price,
                'price_discount': item.price_discount,
                'price_surcharge': item.price_surcharge,
                'price_round': item.price_round,
                'min_quantity': item.min_quantity,
            })
        return {
            'name': rec.name,
            'currency_name': rec.currency_id.name,
            'active': rec.active,
            'items': items,
            '_match_key': {'name': rec.name},
        }
