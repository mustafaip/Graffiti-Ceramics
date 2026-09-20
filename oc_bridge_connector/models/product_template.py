# -*- coding: utf-8 -*-
from odoo import models, api


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'oc.connector.mixin']

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
            return  # Enterprise is the master for products
        self._oc_push(operation, 'product.template', self._oc_product_payload)

    def _oc_product_payload(self, rec):
        return {
            'name': rec.name,
            'default_code': rec.default_code,
            'barcode': rec.barcode,
            'type': rec.type,
            'list_price': rec.list_price,
            'standard_price': rec.standard_price,
            'uom_name': rec.uom_id.name,
            'sale_ok': rec.sale_ok,
            'active': rec.active,
            '_match_key': {'default_code': rec.default_code, 'name': rec.name},
        }
