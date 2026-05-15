# -*- coding: utf-8 -*-
import base64
from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """
        After rendering the standard quotation PDF, append any
        is_so_design_doc PDF attachments linked to the sale.order records.
        """
        result, content_type = super()._render_qweb_pdf(
            report_ref, res_ids=res_ids, data=data
        )

        # Only intercept sale order reports
        report = self._get_report(report_ref)
        if report.model != 'sale.order' or not res_ids:
            return result, content_type

        # Collect all PDF design doc attachments across the printed records
        pdf_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', 'in', res_ids),
            ('is_so_design_doc', '=', True),
            ('mimetype', 'like', 'pdf'),
        ])

        if not pdf_attachments:
            return result, content_type

        # Merge using pypdf (bundled with Odoo) or PyPDF2
        try:
            from pypdf import PdfWriter, PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfWriter, PdfReader
            except ImportError:
                # Neither available — return without merging
                return result, content_type

        import io

        writer = PdfWriter()

        # Add all pages from the main rendered report
        main_reader = PdfReader(io.BytesIO(result))
        for page in main_reader.pages:
            writer.add_page(page)

        # Append each design doc PDF
        for att in pdf_attachments:
            try:
                att_bytes = base64.b64decode(att.datas)
                att_reader = PdfReader(io.BytesIO(att_bytes))
                for page in att_reader.pages:
                    writer.add_page(page)
            except Exception:
                # Skip corrupt/unreadable attachments silently
                continue

        output = io.BytesIO()
        writer.write(output)
        merged_pdf = output.getvalue()

        return merged_pdf, content_type
