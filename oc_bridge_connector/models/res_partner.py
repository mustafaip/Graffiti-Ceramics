# -*- coding: utf-8 -*-
from odoo import models, api


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'oc.connector.mixin']

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
            return  # Enterprise is the master for customers
        self._oc_push(operation, 'res.partner', self._oc_partner_payload)

    def _oc_partner_payload(self, rec):
        return {
            'name': rec.name,
            'is_company': rec.is_company,
            'email': rec.email,
            'phone': rec.phone,
            'street': rec.street,
            'street2': rec.street2,
            'city': rec.city,
            'zip': rec.zip,
            'country_code': rec.country_id.code or False,
            'state_name': rec.state_id.name or False,
            'vat': rec.vat,
            'ref': rec.ref,
            '_match_key': {'vat': rec.vat, 'email': rec.email, 'name': rec.name},
        }
