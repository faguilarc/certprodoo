import base64
import io
from datetime import datetime

from odoo import fields, models, api
from xlsxwriter.utility import xl_rowcol_to_cell


class ReportDocumentsRequired(models.AbstractModel):
    _name = 'report.nomenclators.report_documents_required'
    _description = 'Reporte de documentos requeridos'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['nomenclators.documents_required'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': self.env['nomenclators.documents_required'],
            'docs': docs
        }