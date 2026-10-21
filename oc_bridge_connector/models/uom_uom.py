# -*- coding: utf-8 -*-
from odoo import models, api


class UomUom(models.Model):
    _name = 'uom.uom'
    _inherit = ['uom.uom', 'oc.connector.mixin']

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
        self._oc_push(operation, 'uom.uom', self._oc_uom_payload)

    def _oc_uom_payload(self, rec):
        # Odoo 20 units are hierarchical: a unit is expressed relative to a
        # "reference" unit (relative_uom_id x relative_factor). There is no
        # uom.category / uom_type / rounding any more.
        return {
            'name': rec.name,
            'relative_uom_name': rec.relative_uom_id.name or False,
            'relative_factor': rec.relative_factor,
            'active': rec.active,
            '_match_key': {'name': rec.name},
        }
