from odoo import models, fields, api

class PublicRequest(models.Model):
    _name = 'professional_registers.public_request'
    _description = 'Configuración de Campos Públicos'

    request_id = fields.Many2one('professional_registers.professional_request', 'Solicitud')
    
    # Campos booleanos para datos personales
    show_name = fields.Boolean('Mostrar Nombre', default=False)
    show_first_last_name = fields.Boolean('Mostrar Primer Apellido', default=False)
    show_second_last_name = fields.Boolean('Mostrar Segundo Apellido', default=False)
    show_nationality_id = fields.Boolean('Mostrar Nacionalidad', default=False)
    show_identity = fields.Boolean('Mostrar Identidad', default=False)
    show_sex = fields.Boolean('Mostrar Sexo', default=False)
    show_image = fields.Boolean('Mostrar Imagen', default=False)

    # Campos booleanos para contacto
    show_phone = fields.Boolean('Mostrar Teléfono', default=False)
    show_email = fields.Boolean('Mostrar Email', default=False)
    show_address = fields.Boolean('Mostrar Dirección', default=False)
    show_country = fields.Boolean('Mostrar País', default=False)
    show_country_states = fields.Boolean('Mostrar Estado/Provincia', default=False)
    show_city = fields.Boolean('Mostrar Ciudad', default=False)

    # Campos booleanos para datos académicos
    show_teaching_level = fields.Boolean('Mostrar Nivel de Enseñanza', default=False)
    show_study_center = fields.Boolean('Mostrar Centro de Estudio', default=False)
    show_degree_date = fields.Boolean('Mostrar Fecha de Título', default=False)
    show_volume = fields.Boolean('Mostrar Volumen', default=False)
    show_folio = fields.Boolean('Mostrar Folio', default=False)
    show_number = fields.Boolean('Mostrar Número', default=False)

    # Campos booleanos para datos profesionales
    show_profession = fields.Boolean('Mostrar Profesión', default=False)
    show_specialties = fields.Boolean('Mostrar Especialidades', default=False)
    show_teaching_category = fields.Boolean('Mostrar Categoría Docente', default=False)
    show_teaching_category_date = fields.Boolean('Mostrar Fecha Categoría Docente', default=False)
    show_degree_sciences = fields.Boolean('Mostrar Grado Científico', default=False)
    show_degree_sciences_year = fields.Boolean('Mostrar Año Grado Científico', default=False)
    show_unaicc_date = fields.Boolean('Mostrar Fecha UNAICC', default=False)

    # Campos booleanos para trayectoria laboral e idiomas
    show_history_work = fields.Boolean('Mostrar Vínculo Laboral', default=False)
    show_professional_language = fields.Boolean('Mostrar Idiomas', default=False)

    # New field for required documents
    show_required_documents = fields.Many2many('nomenclators.documents_required','public_field_fields_docr_rel',
                                               string='Documentos Requeridos Públicos')

    @api.model
    def create(self, vals):
        """Evitar duplicados por solicitud"""
        if vals.get('request_id'):
            existing = self.search([('request_id', '=', vals['request_id'])], limit=1)
            if existing:
                return existing
        return super().create(vals)