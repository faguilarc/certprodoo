from odoo import models, fields, api
import json
from lxml import etree


class ProfessionalRequestPublicField(models.Model):
    #Modelo mas estable y funcional
    _name = 'professional_registers.public_field'
    _description = 'Campos públicos de Professional Request'

    CATEGORY_FIELDS = {
        'personal': ['name', 'first_last_name', 'second_last_name', 'nationality_id', 'identity', 'sex', 'image'],
        'contact': ['phone', 'email', 'address', 'country', 'country_states', 'city'],
        'academic': ['teaching_level', 'study_center', 'degree_date', 'volume', 'folio', 'number'],
        'professional': ['profession', 'specialties', 'teaching_category', 'teaching_category_date',
                         'degree_sciences', 'degree_sciences_year', 'unaicc_date'],
        'work': ['history_work'],
        'language': ['professional_language']
    }

    category = fields.Selection([
        ('personal', 'Datos Personales'),
        ('contact', 'Datos de Contacto'),
        ('academic', 'Datos Académicos'),
        ('professional', 'Datos Profesionales'),
        ('work', 'Trayectoria Laboral'),
        ('language', 'Idiomas')
    ], string="Categoría", required=True)

    # Campo relacionado a ir.model.fields
    fields_ids = fields.Many2many(
        'ir.model.fields',
        'public_field_fields_rel',
        'public_field_id',
        'field_id',
        string="Campos",
        domain="[('model', '=', 'professional_registers.professional_request')]"
    )

    # Eliminar el método _get_field_domain ya que no es necesario
    
    @api.onchange('category')
    def _onchange_category(self):
        if not self.category:
            self.fields_ids = False
        return {
            'domain': {
                'fields_ids': [
                    ('model', '=', 'professional_registers.professional_request'),
                    ('name', 'in', self.CATEGORY_FIELDS.get(self.category, []))
                ]
            }
        }

    active = fields.Boolean(default=True)
    request_id = fields.Many2one('professional_registers.professional_request', string='Solicitud')

    # Cambiar a Many2many para permitir operaciones de escritura
    existing_public_fields = fields.Many2many(
        'professional_registers.public_field',
        compute='_compute_existing_public_fields',
        string='Campos Públicos Existentes'
    )

    @api.depends('request_id')
    def _compute_existing_public_fields(self):
        for record in self:
            if record.request_id:
                # Buscar todos los campos públicos asociados a esta solicitud
                record.existing_public_fields = self.env['professional_registers.public_field'].search([
                    ('request_id', '=', record.request_id.id)
                ])
            else:
                record.existing_public_fields = False

    # Método para eliminar registros
    def unlink(self):
        """Sobrescribir método unlink para lógica adicional"""
        # Guardar información antes de eliminar
        request_ids = self.mapped('request_id').ids

        # Ejecutar eliminación normal
        res = super().unlink()

        # Actualizar campo computado en registros padre
        padres = self.env['professional_registers.public_field'].search([
            ('id', 'in', request_ids)
        ])

        for padre in padres:
            padre._compute_existing_public_fields()

        return res

    # Método auxiliar para obtener las opciones desde el widget
    def get_field_selection_options(self):
        return self._get_fields_selection()

    # Métodos helper para trabajar con valores múltiples
    def get_selected_field_values(self):
        """Retorna lista de valores seleccionados"""
        if self.field_name:
            return self.field_name.split(',')
        return []

    def set_selected_field_values(self, values):
        """Establece valores seleccionados desde una lista"""
        if isinstance(values, list):
            self.field_name = ','.join(values) if values else False
        else:
            self.field_name = values

    def action_save(self):
        self.ensure_one()
        if self.fields_ids:
            for field in self.fields_ids:
                self.env['professional_registers.public_field'].create({
                    'request_id': self.request_id.id,
                    'category': self.category,
                    'fields_ids': field,
                    'active': self.active
                })


    @api.model
    def create(self, vals):
        # 1. Verificar si tenemos los campos necesarios para buscar duplicados
        request_id = vals.get('request_id')
        field_id = vals.get('field_id')  # Usar field_id en lugar de field_name

        # 2. Solo buscar si tenemos ambos valores
        if request_id and field_id:
            # Buscar duplicados usando el nuevo campo field_id
            existing = self.search([
                ('request_id', '=', request_id),
                ('field_id', '=', field_id)
            ], limit=1)  # Limitar a 1 resultado para eficiencia

            if existing:
                return existing[0]  # Retornar registro existente

        # 3. Crear nuevo registro si no hay duplicados
        return super().create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=False)
        if view_type == 'form':
            # Forzar modo "editable" en el árbol anidado
            doc = etree.XML(res['arch'])
            for tree in doc.xpath("//tree"):
                tree.set('edit', 'false')
                tree.set('delete', 'true')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


