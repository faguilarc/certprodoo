from odoo import fields, models, api, exceptions
from datetime import datetime, timedelta, date

from odoo.http import request


class GenerateRequestWizard(models.Model):
    _name = 'professional_registers.request_wizard'
    _description = 'Generar solicitud'

    request_date = fields.Date('Fecha de solicitud', default=datetime.utcnow().date())
    procedure_type = fields.Many2one('nomenclators.procedure_types', string="Tipo de trámite")

    documents_required = fields.One2many('professional_registers.pr_document', 'request_wizard',
                                         string="Documentos requeridos")
    professions = fields.Many2one('nomenclators.professions', string="Profesión", )

    # others_professions = fields.Many2many('professional_registers.others_professions',
    #                                       relation='request_quizard_other_professions',
    #                                      string="Otras profesiones")
    # profile = fields.Many2one('professional_registers.profile', string="Perfil",)

    @api.onchange('procedure_type')
    def onchange_procedure_type(self):
        if self.procedure_type:
            id_profile = self._context.get('profile')

            # Rellenar los documentos requeridos
            documents = self.env['nomenclators.documents_required'].search(
                [('procedure1', '=', int(self.procedure_type.id))])
            document_list = []

            documents_temp = []
            if id_profile:
                profile = self.env['professional_registers.profile'].search([('id', '=', int(id_profile))])

                for register in profile.documents_required:
                    attachment = []
                    for reg in register.attachment_ids:
                        attachment.append(reg.id)

                    documents_temp.append(register.documents.id)
                    document_list.append((0, 0, {
                        'profile': id_profile,
                        'request_wizard': self.id,
                        'documents': register.documents.id,
                        'attachment_ids': [[6, 0, attachment]],
                    }))

            for register in documents:
                if register.id not in documents_temp:
                    document_list.append((0, 0, {
                        'profile': id_profile,
                        'request_wizard': self.id,
                        'documents': register.id,
                        'attachment_ids': False,
                    }))

            self.documents_required = [[6, 0, []]]
            self.documents_required = document_list

            # Rellenar el campo de profesiones
            profile = self.env['professional_registers.profile'].search([('id', '=', int(id_profile))])
            op = self.env['professional_registers.others_professions'].search([('profile', '=', int(id_profile))])

            # Buscar profesiones relacionadas con el perfil
            # Limitar el número de profesiones mostradas en la vista basándose en la longitud de la lista
            limit = len(op)  # Ajusta el número 10 según tus necesidades

            domain = [
                '|',
                ('id', '=', profile.profession.id),
                ('id', '=', op.professions_id.id)
            ]
            self.professions = self.env['nomenclators.professions'].search(
                ['|', ('id', '=', int(profile.profession.id)), ('id', '=', op.professions_id.id)])[0]

    def get_default_state(self):
        model = self.env['ir.model'].search([('model', '=', 'professional_registers.professional_request')])
        states = self.env['security.state_configuration'].search([('model', '=', int(model.id))], order="priority asc")
        if states:
            return states[1].id
        return 0

    def generate_request(self):

        request_number = self.env['professional_registers.professional_request'].get_request_number()
        id_profile = self._context.get('profile')
        profile = self.env['professional_registers.profile'].search([('id', '=', int(id_profile))])

        request = self.env['professional_registers.professional_request'].sudo().create({
            'request_number': request_number,
            'name': profile.name,
            'first_last_name': profile.first_last_name,
            'second_last_name': profile.second_last_name,
            'full_name': profile.full_name,
            'nationality_id': profile.nationality_id.id,
            'identity': profile.identity,
            'id_fuc': profile.id_fuc,
            'sex': profile.sex,
            'address': profile.address,
            'country': profile.country.id,
            'country_states': profile.country_states.id,
            'city': profile.city.id,
            'user': profile.user,
            'user_id': profile.user_id.id,
            'id_user_register': profile.user_id.id,
            'register_user': 'Registro online',
            'password': '****',
            'observation': profile.observation,
            'register_type': 'register',
            'states': self.get_default_state(),
            'priority': 1,
            'is_inscription_fuc': True if profile.nationality_id.validate_fuc else False,
            'date_request': datetime.utcnow().date().today(),
            'is_register_online': True,
            'phone': profile.phone,
            'profession': self.professions.id,
            'email': profile.email,
            'teaching_level': profile.teaching_level,
            'procedure_type': self.procedure_type.id,
            # a partir de aqui buscar en dependencia del other professions
            'specialties': profile.specialties.id,
            'volume': profile.volume,
            'folio': profile.folio,
            'number': profile.number,
            'study_center': profile.study_center,
            'degree_date': profile.degree_date,
        })
        msg = "Se ha generado la solicitud No: " + str(request.request_number)
        self.env.user.notify_warning(
            message=msg)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'professional_registers.professional_request',
            'name': 'Solicitud del profesional',
            'view_mode': 'form',
            'res_id': request.id,
            'target': 'main',
            'clear_breadcrumbs': True,
        }

    def accept(self):
        return {"type": "ir.actions.act_window_close"}

    def close(self):
        self.env.user.active = False

        request.session.logout()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/login?redirect=/web',  # Redirige a la página principal después del login
            'target': 'self',
        }
