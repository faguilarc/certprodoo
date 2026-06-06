# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class DashboardSecurity(models.Model):
    _name = "nomenclators.dashboard"
    _description = "Estadísticas de Nomencladores"

    name = fields.Char("Estadísticas")

    @api.model
    def get_count_professions(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        professions = self.env["nomenclators.professions"].search([('company_id', 'in', company_access.company_ids.ids)])
        quantity = len(professions)
        return quantity

    @api.model
    def get_count_specialties(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        specialties = self.env["nomenclators.specialties"].search(
            [('company_id', 'in', company_access.company_ids.ids)])
        quantity = len(specialties)
        return quantity

    @api.model
    def get_count_study_centers(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        study_centers = self.env["nomenclators.study_centers"].search(
            [('company_id', 'in', company_access.company_ids.ids)])
        quantity = len(study_centers)
        return quantity

    @api.model
    def get_count_teaching_categories(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        teaching_categories = self.env["nomenclators.teaching_categories"].search(
            [('company_id', 'in', company_access.company_ids.ids)])
        quantity = len(teaching_categories)
        return quantity

    @api.model
    def get_count_documents_required(self, values=None):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])
        company_access = (
            self.env["res.users"].sudo().search([("id", "=", int(user.id))])
        )

        teaching_categories = self.env["nomenclators.documents_required"].search(
            [('company_id', 'in', company_access.company_ids.ids)])
        quantity_inscription = 0
        quantity_update = 0
        quantity_renewal = 0
        for tc in teaching_categories:
            if tc.procedure1.name == 'Solicitud de inscripción':
                quantity_inscription = quantity_inscription + 1
            elif tc.procedure1.name == 'Actualización':
                quantity_update = quantity_update + 1
            elif tc.procedure1.name == 'Renovación':
                quantity_renewal = quantity_renewal + 1

        quantities = []
        quantities.append({
            'inscription': quantity_inscription,
            'update': quantity_update,
            'renewal': quantity_renewal,
        })
        return quantities

    @api.model
    def get_full_data(self, values=None):
        info = []

        total_professions = self.get_count_professions(values)
        total_specialties = self.get_count_specialties(values)
        total_get_count_study_centers = self.get_count_study_centers(values)
        total_get_count_teaching_categories = self.get_count_teaching_categories(values)
        total_documents_required = self.get_count_documents_required()
        total_inscription = total_documents_required[0]['inscription']
        total_update = total_documents_required[0]['update']
        total_renewal = total_documents_required[0]['renewal']

        info.append(
            {
                "professions": total_professions,
                'college': total_get_count_study_centers,
                'categories': total_get_count_teaching_categories,
                'specialities': total_specialties,
                'documents_inscriptions': total_inscription,
                'documents_update': total_update,
                'documents_renewal': total_renewal,
            }
        )
        return info
