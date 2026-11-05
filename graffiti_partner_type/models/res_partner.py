import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import SQL


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # (Re)define the Individual / Company selector so it works regardless of
    # whether the base module still ships it.
    company_type = fields.Selection(
        string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Company')],
        compute='_compute_gc_company_type',
        inverse='_inverse_gc_company_type',
    )
    same_phone_partner_id = fields.Many2one(
        'res.partner',
        string='Partner with same phone',
        compute='_compute_same_phone_partner_id',
        compute_sudo=True,
    )

    # ------------------------------------------------------------------
    # Individual / Company
    # ------------------------------------------------------------------
    @api.depends('is_company')
    def _compute_gc_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'person'

    def _inverse_gc_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'

    @api.onchange('company_type')
    def _onchange_gc_company_type(self):
        for partner in self:
            partner.is_company = partner.company_type == 'company'

    # ------------------------------------------------------------------
    # TRN mandatory for companies
    # ------------------------------------------------------------------
    @api.constrains('is_company', 'vat', 'type', 'parent_id')
    def _check_company_has_trn(self):
        ctx = self.env.context
        if ctx.get('skip_trn_check') or ctx.get('install_mode'):
            return
        for partner in self:
            if (
                partner.is_company
                and (partner.type or 'contact') == 'contact'
                and not partner.parent_id
                and not (partner.vat or '').strip()
            ):
                raise ValidationError(_(
                    "TRN (Tax ID) is mandatory when the contact is a Company: %s",
                    partner.display_name or partner.name or '',
                ))

    # ------------------------------------------------------------------
    # Duplicate phone warning (individuals only)
    # ------------------------------------------------------------------
    @api.model
    def _gc_phone_key(self, number):
        """Digits only, last 9 digits (so +971 50 123 4567 == 0501234567)."""
        digits = re.sub(r'\D', '', number or '')
        return digits[-9:] if len(digits) >= 6 else False

    @api.depends('phone', 'mobile', 'is_company', 'parent_id')
    def _compute_same_phone_partner_id(self):
        for partner in self:
            partner.same_phone_partner_id = False
            if partner.is_company:
                continue
            keys = {
                k for k in (
                    self._gc_phone_key(partner.phone),
                    self._gc_phone_key(partner.mobile),
                ) if k
            }
            if not keys:
                continue
            self.env.cr.execute(SQL(
                """
                SELECT id FROM res_partner
                 WHERE active IS TRUE
                   AND id != %s
                   AND (parent_id IS NULL OR parent_id != %s)
                   AND (
                        right(regexp_replace(coalesce(phone, ''), '[^0-9]', '', 'g'), 9) = ANY(%s)
                     OR right(regexp_replace(coalesce(mobile, ''), '[^0-9]', '', 'g'), 9) = ANY(%s)
                   )
                 ORDER BY id
                 LIMIT 1
                """,
                partner._origin.id or 0,
                partner.parent_id.id or 0,
                list(keys),
                list(keys),
            ))
            row = self.env.cr.fetchone()
            if row:
                partner.same_phone_partner_id = row[0]
