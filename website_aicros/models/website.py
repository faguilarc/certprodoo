# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Dashboard(models.Model):
    _name = 'website_model'

    error_message = fields.Char(string="Error Message")

    @api.model
    def get_professions(self):
        professions = self.env['nomenclators.professions'].search([], order='name asc')

        return professions

    @api.model
    def get_nationalities(self):
        professions = self.env['nomenclators.nationality'].search([])
        return professions

    @api.model
    def get_specialties(self):
        specialties = self.env['nomenclators.specialties'].search([])
        return specialties

    @api.model
    def get_str_structure(self):
        structures = self.env['nomenclators.structures'].search([], limit=1)
        return structures

    @api.model
    def get_str_inscription(self):
        enrrols = self.env['nomenclators.who_enrrols'].search([], limit=1)
        return enrrols

    @api.model
    def get_str_normative(self):
        normative = self.env['nomenclators.normative'].sudo().search([])
        for n in normative:
            for attachment in n.attachment_ids:
                attachment.write({'public': True})
        return normative

    @api.model
    def get_str_relations_documents(self):
        procedure_types = self.env['nomenclators.procedure_types'].search([])
        documents = []
        for pt in procedure_types:
            relations_documents = self.env['nomenclators.documents_required'].search([('procedure1', '=', int(pt.id))], order="order asc")
            for rd in relations_documents:
                documents.append({
                    'procedure': pt.name,
                    'document': rd.name,
                })
        return documents


    @api.model
    def get_register_inscription(self, params=None):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.inscription')])
        state_approved = self.env['security.state_configuration'].search([('model', '=', int(model.id)), ('priority', '=', 1)])
        domain = [('states', '=', state_approved.id)]
        if params:
            profession_param = ''
            if 'professions' in params:
                profession_param = params['professions']
            nationality_param = ''
            if 'nationalities' in params:
                nationality_param = params['nationalities']
            name_param = ''
            if 'contact_name' in params:
                name_param = params['contact_name']
            last_name_param = ''
            if 'contact_last_name' in params:
                last_name_param = params['contact_last_name']
            register_number_param = ''
            if 'register_number' in params:
                register_number_param = params['register_number']
            specialties_param = ''
            if 'specialties' in params:
                specialties_param = params['specialties']

            if profession_param != '' and profession_param != 'Todas':
                domain.append(('profession', '=', int(profession_param)))

            if nationality_param != '':
                domain.append(('nationality_id', '=', int(nationality_param)))

            if name_param != '':
                str_busqueda = '%' + str(name_param) + '%'
                domain.append(('name', 'ilike', str(str_busqueda)))

            if last_name_param != '':
                str_busqueda = '%' + str(last_name_param) + '%'
                domain.append('|')
                domain.append(('first_last_name', 'ilike', str(str_busqueda)))
                domain.append(('second_last_name', 'ilike', str(str_busqueda)))

            if register_number_param != '':
                domain.append(('inscription_number', '=', str(register_number_param)))

            if specialties_param != '':
                domain.append(('specialties', '=', int(specialties_param)))

        register_inscriptions = self.env['professional_registers.inscription'].search(domain)

        result = []
        for ri in register_inscriptions:
            last_name = ri.first_last_name + ' ' + ri.second_last_name
            result.append({
                'name': ri.name,
                'last_name': last_name,
                'register_number': ri.inscription_number,
                'profesion': ri.profession.name,
                'nationality': ri.nationality_id.name,
                'specialties': ri.specialties.name,
                'request_id':ri.request_id.id

            })
        return result

