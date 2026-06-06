from odoo import fields, models, api
from datetime import datetime, timedelta, date

class DocumentsRequiredReportWizard(models.Model):
    _name = 'report.documents_required_wizard'
    _description = 'Reporte de documentos requeridos'

    procedure_type = fields.Many2one('nomenclators.procedure_types', string="Trámite")

    def get_documents(self):
        documents = self.env['nomenclators.documents_required'].search([('procedure1', '=', int(self.procedure_type.id))])
        count = 1
        result = []
        for d in documents:
            result.append({
                'no': count,
                'name': d.name,
                'description': d.description
            })
            count = count + 1
        return result

    def show_report(self):
        documents = self.get_documents()
        data = {
           'documents': documents,
            'procedure_type': self.procedure_type.name,
        }
        return self.env.ref('nomenclators.documents_required_detail').report_action(self, data)