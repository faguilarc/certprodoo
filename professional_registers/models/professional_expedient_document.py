from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExpedientDocument(models.Model):
    _name = 'professional_registers.expedient_document'
    _description = 'Documentos del Expediente'
    _order = 'date desc'

    expedient_id = fields.Many2one('professional_registers.expedient', string='Expediente', required=True,
                                   ondelete='cascade')
    name = fields.Char('Descripción', required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Archivo', required=True)
    file_name = fields.Char('Nombre de Archivo', compute='_compute_file_name', store=True)
    date = fields.Datetime('Fecha', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Subido por', required=True)

    # Clasificación del documento
    document_type = fields.Selection([
        ('request', 'Solicitud'),
        ('certificate', 'Certificado'),
        ('identification', 'Identificación'),
        ('academic', 'Académico'),
        ('laboral', 'Laboral'),
        ('communication', 'Comunicación'),
        ('other', 'Otro'),
    ], string='Tipo de Documento', default='other')

    # Origen del documento
    source_model = fields.Char('Modelo de Origen')
    source_id = fields.Integer('ID de Origen')

    # Observaciones
    notes = fields.Text('Notas')

    # Campo Reference que enlaza al registro origen
    source_reference = fields.Reference(
        selection='_get_source_models',
        string='Registro Origen',
        compute='_compute_source_reference',
        store=True,  # Almacenado para permitir búsquedas y filtros
        help="Documento original del cual proviene este archivo (solicitud, actualización, etc.)"
    )

    @api.depends('source_model', 'source_id')
    def _compute_source_reference(self):
        for record in self:
            if record.source_model and record.source_id:
                record.source_reference = f'{record.source_model},{record.source_id}'
            else:
                record.source_reference = False

    @api.model
    def _get_source_models(self):
        """Devuelve la lista de modelos que pueden ser origen de documentos."""
        return [
            ('professional_registers.professional_request', 'Solicitud'),
            ('professional_registers.professional_request_update', 'Actualización'),
            ('professional_registers.claim_request', 'Reclamación'),
            ('professional_registers.inscription', 'Inscripción'),
        ]

    @api.depends('attachment_id', 'attachment_id.name')
    def _compute_file_name(self):
        for record in self:
            record.file_name = record.attachment_id.name if record.attachment_id else False

    def action_download(self):
        self.ensure_one()
        if not self.attachment_id:
            raise ValidationError("No hay archivo adjunto para descargar.")
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'self',
        }