# -*- coding: utf-8 -*-
from odoo import api, fields, models

SQM_PER_PIECE_HELP = (
    'Area (in the product\'s unit, normally SQM) of ONE piece, e.g. 0.72.')
PIECES_PER_BOX_HELP = (
    'Number of pieces in ONE box, e.g. 2. Together with "SQM per Piece" this '
    'gives the SQM per box that sale quantities are rounded up to.')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Stored per variant: every size packs a different number of pieces.
    sqm_per_piece = fields.Float(
        string='SQM per Piece', digits=(16, 4), help=SQM_PER_PIECE_HELP)
    pieces_per_box = fields.Integer(
        string='Pieces per Box', help=PIECES_PER_BOX_HELP)
    sqm_per_box = fields.Float(
        string='SQM per Box', digits=(16, 4),
        compute='_compute_sqm_per_box')

    @api.depends('sqm_per_piece', 'pieces_per_box')
    def _compute_sqm_per_box(self):
        for product in self:
            product.sqm_per_box = product.sqm_per_piece * product.pieces_per_box


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Same pattern as Internal Reference / Barcode: stored on the variant,
    # edited on the template while it has a single variant.
    sqm_per_piece = fields.Float(
        string='SQM per Piece', digits=(16, 4),
        compute='_compute_box_factors', inverse='_inverse_sqm_per_piece',
        help=SQM_PER_PIECE_HELP)
    pieces_per_box = fields.Integer(
        string='Pieces per Box',
        compute='_compute_box_factors', inverse='_inverse_pieces_per_box',
        help=PIECES_PER_BOX_HELP)
    sqm_per_box = fields.Float(
        string='SQM per Box', digits=(16, 4),
        compute='_compute_box_factors')

    @api.depends('product_variant_ids.sqm_per_piece', 'product_variant_ids.pieces_per_box')
    def _compute_box_factors(self):
        for template in self:
            variants = template.product_variant_ids
            single = len(variants) == 1
            template.sqm_per_piece = variants.sqm_per_piece if single else 0.0
            template.pieces_per_box = variants.pieces_per_box if single else 0
            template.sqm_per_box = template.sqm_per_piece * template.pieces_per_box

    def _inverse_sqm_per_piece(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.sqm_per_piece = template.sqm_per_piece

    def _inverse_pieces_per_box(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.pieces_per_box = template.pieces_per_box

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        # The inverse runs before the variants exist on create: set again.
        for template, vals in zip(templates, vals_list):
            if len(template.product_variant_ids) == 1:
                variant_vals = {k: vals[k] for k in ('sqm_per_piece', 'pieces_per_box') if vals.get(k)}
                if variant_vals:
                    template.product_variant_ids.write(variant_vals)
        return templates
