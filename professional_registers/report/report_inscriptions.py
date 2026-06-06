import base64
import io
from datetime import datetime

from odoo import fields, models, api
from xlsxwriter.utility import xl_rowcol_to_cell


class ReportInscriptions(models.AbstractModel):
    _name = 'report.professional_registers.report_inscriptions'
    _description = 'Reporte de inscripciones'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['professional_registers.inscription'].browse(docids)
        logo = self.env['nomenclators.logo'].search([('name', '=', 'Escudo')])
        return {
            'doc_ids': docids,
            'doc_model': self.env['professional_registers.inscription'],
            'docs': docs,
            'company': logo[0]
        }