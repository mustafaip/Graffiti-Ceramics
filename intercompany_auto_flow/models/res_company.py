# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ── Intercompany Auto Flow Settings ──────────────────────────────────────
    intercompany_auto_flow = fields.Boolean(
        string='Enable Intercompany Auto Flow',
        default=False,
        help='When enabled, selling a product with no local stock will '
             'automatically trigger a purchase order from a sibling company '
             'that has the stock available.',
    )

    intercompany_sale_auto_confirm = fields.Boolean(
        string='Auto-Confirm Intercompany Sales Orders',
        default=True,
        help='Automatically confirm the sales order generated in the '
             'supplying company when an intercompany PO is created.',
    )

    intercompany_purchase_auto_confirm = fields.Boolean(
        string='Auto-Confirm Intercompany Purchase Orders',
        default=True,
        help='Automatically confirm the purchase order generated in the '
             'buying company.',
    )

    intercompany_auto_validate_pickings = fields.Boolean(
        string='Auto-Validate Stock Moves',
        default=False,
        help='Automatically validate the delivery in the supplying company '
             'and the receipt in the buying company. '
             'Enable this when companies share the same physical warehouse '
             'and stock moves are purely bookkeeping entries between legal entities.',
    )

    intercompany_search_all_companies = fields.Boolean(
        string='Search All Companies for Stock',
        default=True,
        help='Search every sibling company in the database. '
             'If disabled, only companies listed in the allowed partners '
             'field will be searched.',
    )

    intercompany_allowed_company_ids = fields.Many2many(
        comodel_name='res.company',
        relation='company_intercompany_allowed_rel',
        column1='company_id',
        column2='allowed_company_id',
        string='Allowed Supplier Companies',
        help='Limit intercompany stock sourcing to these companies. '
             'Only used when "Search All Companies" is disabled.',
    )

    intercompany_stock_route_id = fields.Many2one(
        comodel_name='stock.route',
        string='Intercompany Route',
        help='Optional: stock route to assign to intercompany PO lines.',
        domain=[('supplied_wh_id', '!=', False)],
    )

    intercompany_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Intercompany Partner',
        help='Partner record that represents THIS company when it acts as '
             'a supplier to sibling companies. '
             'Leave empty to use the company partner automatically.',
        compute='_compute_intercompany_partner_id',
        store=True,
        readonly=False,
    )

    @api.depends('partner_id')
    def _compute_intercompany_partner_id(self):
        for company in self:
            company.intercompany_partner_id = company.partner_id

    def _get_intercompany_supplier_candidates(self):
        """Return companies that can supply stock to self."""
        self.ensure_one()
        if self.intercompany_search_all_companies:
            return self.search([('id', '!=', self.id), ('intercompany_auto_flow', '=', True)])
        return self.intercompany_allowed_company_ids.filtered(
            lambda c: c.intercompany_auto_flow
        )
