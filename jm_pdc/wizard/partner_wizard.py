from odoo import api, fields, models
from odoo.exceptions import UserError


class PartnerWizard(models.TransientModel):
    _name = "partner.wizard"
    _description = "Wizard for Showing Partners from pdc.wizard model"

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    partner_ids = fields.Many2many(
        "res.partner", string="Partners",
        domain="[('id', 'in', allowed_partner_ids)]")
    # FIX #12: @api.depends() with no args — allowed_partner_ids does not
    # depend on partner_ids; it depends on all pdc.wizard records.
    allowed_partner_ids = fields.Many2many(
        "res.partner", compute="_compute_allowed_partners")
    selected_state = fields.Selection(
        [('draft', 'Draft'), ('registered', 'Registered'), ('returned', 'Returned'),
         ('deposited', 'Deposited'), ('bounced', 'Bounced'), ('done', 'Done'),
         ('cancel', 'Cancelled')],
        string="State")

    @api.depends()
    def _compute_allowed_partners(self):
        pdc_records = self.env['pdc.wizard'].search([])
        partner_ids = [r.partner_id.id for r in pdc_records if r.partner_id]
        for rec in self:
            rec.allowed_partner_ids = [(6, 0, partner_ids)]

    def button_print_report(self):
        self.ensure_one()
        domain = []
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.selected_state:
            domain.append(('state', '=', self.selected_state))
        if self.from_date and self.to_date:
            domain.append(('due_date', '>=', self.from_date))
            domain.append(('due_date', '<=', self.to_date))

        pdc_records = self.env['pdc.wizard'].search(domain)
        if not pdc_records:
            raise UserError("No records found for the selected filters.")

        return self.env.ref('jm_pdc.pdc_wizard').report_action(pdc_records.ids)


class PDCWizardReport(models.AbstractModel):
    _name = 'report.jm_pdc.report_pdc_payment'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pdc.wizard'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'pdc.wizard',
            'docs': docs,
        }
