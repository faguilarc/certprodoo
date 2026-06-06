import base64
import io
from datetime import datetime

from odoo import fields, models, api
from xlsxwriter.utility import xl_rowcol_to_cell


class ReportIdentity(models.AbstractModel):
    _name = 'report.professional_registers.report_identity'
    _description = 'Reporte de inscripciones'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['professional_registers.identity'].browse(docids)
        id_identity = self._context.get('id_identity')
        identity = self.env['professional_registers.identity'].search([('id', '=', int(id_identity))])
        user_id = identity.inscription_id.request_id.id_user_register.id
        user = self.env['res.users'].search([('id', '=', int(user_id))])
        return {
            'doc_ids': docids,
            'doc_model': self.env['professional_registers.identity'],
            'docs': docs,
            'user': user,

        }