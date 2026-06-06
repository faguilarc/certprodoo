import base64
import io
from datetime import datetime

from odoo import fields, models, api
from xlsxwriter.utility import xl_rowcol_to_cell


class ReportProfessionalRequest(models.AbstractModel):
    _name = 'report.professional_registers.report_professional_request'
    _description = 'Reporte de solicitud del profesional'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['professional_registers.professional_request'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': self.env['professional_registers.professional_request'],
            'docs': docs,
            'data': data,
        }