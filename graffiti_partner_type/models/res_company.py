from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        # Creating a company auto-creates a company partner without TRN;
        # don't block that.
        return super(ResCompany, self.with_context(skip_trn_check=True)).create(vals_list)
