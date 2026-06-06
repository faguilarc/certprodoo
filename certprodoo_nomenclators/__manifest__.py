# -*- coding: utf-8 -*-
{
    "name": "CertProdoo Nomencladores",
    "summary": "Nomencladores del sistema de Registro Profesional",
    "description": """
        Módulo de nomencladores para CertProdoo que proporciona:
        - Nomencladores Profesionales: Profesiones, Especialidades, Nacionalidades
        - Nomencladores de Enseñanza: Niveles, Categorías Docentes, Centros de Estudio
        - Nomencladores Administrativos: Tipos de Trámite, Documentos Requeridos,
          Causas de Estado, Tipos de Entidad
        - Nomencladores Geográficos: Países, Provincias, Municipios, Organismos
        - Nomencladores de Portal: Estructura, Quiénes se Inscriben, Normativas,
          Términos y Condiciones

        Migración de Odoo 14 → 17:
        - fields_view_get + lxml.etree → ir.rule + groups en vistas
        - security.traces → certprodoo.audit.mixin (heredado de certprodoo_base)
        - fields_get → search="False" en vistas
        - nomenclators.logo → campo en res.company
        - professional_language → pasa a Phase 5 (dato del profesional)
        - procedure_suspension_history → pasa a Phase 5/6 (lógica de negocio)
        - BaseNomencatorMixin: code, active, company_id, user_id compartidos
        - Fix: SQL constraints rotos, campos referenciados incorrectamente
    """,
    "author": "Frank Aguilar Caraballo",
    "website": "https://github.com/faguilarc/certprodoo",
    "category": "CertProdoo/Nomenclators",
    "version": "17.0.1.0.0",
    "depends": ["base", "mail", "base_address_city", "certprodoo_base", "certprodoo_security"],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "security/security_rules.xml",
        "data/nationality_data.xml",
        "data/profession_data.xml",
        "data/teaching_level_data.xml",
        "data/teaching_category_data.xml",
        "data/procedure_type_data.xml",
        "data/res_country_state_data.xml",
        "data/res_city_data.xml",
        "data/res_organism_data.xml",
        "data/terms_conditions_data.xml",
        "views/nationality_views.xml",
        "views/profession_views.xml",
        "views/specialty_views.xml",
        "views/teaching_level_views.xml",
        "views/teaching_category_views.xml",
        "views/study_center_views.xml",
        "views/document_required_views.xml",
        "views/procedure_type_views.xml",
        "views/detention_cause_views.xml",
        "views/labour_sector_views.xml",
        "views/normative_views.xml",
        "views/structure_views.xml",
        "views/who_enrolls_views.xml",
        "views/terms_conditions_views.xml",
        "views/res_organism_views.xml",
        "views/res_country_views.xml",
        "views/res_country_state_views.xml",
        "views/res_city_views.xml",
        "views/res_company_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
