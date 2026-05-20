from odoo import models


class PDCPartnerLedgerReportHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _custom_options_initializer(self, report, options, previous_options):
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        # Exclude PDC intermediate accounts from the Partner Ledger
        pdc_customer = self.env.company.pdc_customer
        pdc_vendor = self.env.company.pdc_vendor

        excluded_account_ids = []
        if pdc_customer:
            excluded_account_ids.append(pdc_customer.id)
        if pdc_vendor:
            excluded_account_ids.append(pdc_vendor.id)

        if excluded_account_ids:
            options['forced_domain'] = options.get('forced_domain', []) + [
                ('account_id', 'not in', excluded_account_ids)
            ]
