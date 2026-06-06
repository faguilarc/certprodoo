# -*- coding: utf-8 -*-
import base64
import io
import zipfile

from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta, date
import json

from lxml import etree

from odoo.exceptions import UserError


class DocumentsRequired(models.Model):
    _name = 'nomenclators.documents_required'
    _description = 'Documentos requeridos'
    _rec_name = 'name'

    name = fields.Char('Nombre')
    description = fields.Text('Descripción')
    order = fields.Integer('Órden')
    procedure1 = fields.Many2one('nomenclators.procedure_types', string="Trámite")
    company_id = fields.Many2one('res.company', string="Compañía")
    user_id = fields.Many2one('res.users', string="Usuario")

    is_document_required = fields.Boolean('Documento Obligatorio', default=False)

    is_personal_document = fields.Boolean(
        string='Es Documento Personal',
        default=False,
        help='Si es marcado, este documento se sincroniza globalmente (ej. CI, Currículum).'
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name, order, company_id)',
         'Ya existe un documento requerido con ese nombre para el trámite seleccionado!'),
    ]

    @api.model
    def fields_get(self, fields=None, attributes=None):
        res = super(DocumentsRequired, self).fields_get(fields, attributes=attributes)
        mfields = ['create_uid', 'create_date', 'write_uid', 'write_date', 'user_id', 'company_id', 'order']
        for f in mfields:
            res[f]['searchable'] = False
            res[f]['sortable'] = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DocumentsRequired, self).fields_view_get(view_id=view_id,
                                                             view_type=view_type,
                                                             toolbar=toolbar,
                                                             submenu=submenu)
        doc = etree.XML(res['arch'])

        if not self.env['res.users'].has_group('security.group_professional_superadmin') and not self.env[
            'res.users'].has_group('security.group_professional_managment') and not self.env['res.users'].has_group(
                'security.group_professional_editor_managment'):
            doc.set('create', '0')
            doc.set('edit', '0')
            doc.set('delete', '0')

        res['arch'] = etree.tostring(doc)

        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        user = self.env.user

        # Se verifican los permisos por roles y opciones.

        res = super(DocumentsRequired, self).search_read(domain, fields, offset, limit, order)
        return res

    # Auxiliar
    def is_exist_document(self, order, procedure):
        register = self.env['nomenclators.documents_required'].search(
            [('order', '=', int(order)), ('procedure1', '=', int(procedure))])
        if register:
            raise exceptions.ValidationError('Existe un documento requerido para ese trámite que posee el mismo órden')

    @api.model
    def create(self, vals_list):

        order = vals_list.get('order')
        procedure = vals_list.get('procedure1')
        # verifico que no haya un orden asociado a ese tramite
        self.is_exist_document(order, procedure)

        vals_list["user_id"] = self.env.uid
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        vals_list['company_id'] = user.company_id.id
        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.documents_required')])

        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Creación de documento requerido satisfactoria.'
        })

        return super(DocumentsRequired, self).create(vals_list)

    def write(self, vals):

        if vals.get('order') or vals.get('procedure1'):
            order = vals.get('order') if vals.get('order') else self.order
            procedure = vals.get('procedure1') if vals.get('procedure1') else self.procedure1.id
            # verifico que no haya un orden asociado a ese tramite
            self.is_exist_document(order, procedure)

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.documents_required')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': 'Edición de documento requerido satisfactoria.'
        })
        return super(DocumentsRequired, self).write(vals)

    def unlink(self):
        cantidad_registros = 0
        for reg in self:
            cantidad_registros = cantidad_registros + 1

        # Add traces
        model = self.env['ir.model'].search([('model', '=', 'nomenclators.documents_required')])
        user = self.env['res.users'].search([('id', '=', int(self.env.uid))])
        msg = 'Eliminación de documento requerido satisfactoria.'
        if cantidad_registros > 1:
            msg = 'Eliminación de documentos requerido satisfactoria.'
        self.env['security.traces'].create({
            'register_time': datetime.utcnow(),
            'user': user.name,
            'model': model.id,
            'description': msg
        })

        return super(DocumentsRequired, self).unlink()

    def generate_carnet_zip(self):
        # Tu consulta original
        query = """
            SELECT ia.*
            FROM professional_registers_pr_document pr
            INNER JOIN ir_attachment ia ON pr.id = ia.res_id
            INNER JOIN nomenclators_documents_required ndr ON pr.documents = ndr.id
            WHERE ndr.id = 2
        """

        self.env.cr.execute(query)
        attachments = self.env.cr.dictfetchall()

        if not attachments:
            raise UserError("No se encontraron documentos para carnet")

        # Crear archivo ZIP en memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in attachments:
                data = self.env['ir.attachment'].browse(attachment['id']).datas
                file_content = io.BytesIO(base64.b64decode(data))
                filename = attachment['name']
                zip_file.writestr(filename, file_content.getvalue())

        # Preparar archivo para descarga
        zip_buffer.seek(0)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=ir.attachment&field=datas&filename_field=name&id=%d' % self.save_zip(
                zip_buffer),
            'target': 'self'
        }

    def save_zip(self, zip_buffer):
        attachment = self.env['ir.attachment'].create({
            'name': 'carnet_documents.zip',
            'type': 'binary',
            'datas': base64.b64encode(zip_buffer.getvalue()),
            'store_fname': 'carnet_documents.zip',
            'mimetype': 'application/zip'
        })
        return attachment.id
