# -*- coding: utf-8 -*-
from odoo import models, fields, api


class OcConnectorMapping(models.Model):
    """Correlates a local record with its counterpart on the remote Odoo
    instance, so repeated syncs UPDATE the same record instead of creating
    duplicates.
    """
    _name = 'oc.connector.mapping'
    _description = 'OC Connector: local <-> remote record mapping'
    _rec_name = 'local_model'

    local_model = fields.Char(required=True, index=True)
    local_res_id = fields.Integer(required=True, index=True)
    remote_res_id = fields.Integer(required=True)
    direction = fields.Selection([
        ('push', 'Pushed to remote (I am the sender)'),
        ('pull', 'Received from remote (I am the receiver)'),
    ], required=True, default='push')

    _sql_constraints = [
        ('uniq_local', 'unique(local_model, local_res_id, direction)',
         'A mapping already exists for this record.'),
    ]

    @api.model
    def get_remote_id(self, model, local_id):
        rec = self.search([
            ('local_model', '=', model),
            ('local_res_id', '=', local_id),
            ('direction', '=', 'push'),
        ], limit=1)
        return rec.remote_res_id if rec else False

    @api.model
    def set_mapping(self, model, local_id, remote_id, direction='push'):
        rec = self.search([
            ('local_model', '=', model),
            ('local_res_id', '=', local_id),
            ('direction', '=', direction),
        ], limit=1)
        if rec:
            rec.remote_res_id = remote_id
        else:
            self.create({
                'local_model': model,
                'local_res_id': local_id,
                'remote_res_id': remote_id,
                'direction': direction,
            })

    @api.model
    def get_local_id(self, model, remote_id):
        rec = self.search([
            ('local_model', '=', model),
            ('remote_res_id', '=', remote_id),
            ('direction', '=', 'pull'),
        ], limit=1)
        return rec.local_res_id if rec else False
