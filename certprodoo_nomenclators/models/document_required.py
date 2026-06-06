# -*- coding: utf-8 -*-
"""
DocumentRequired — Nomenclador de Documentos Requeridos.

En O14 era nomenclators.documents_required.
Mejoras O17:
- Fix: usa procedure_type_id en vez de procedure1 (nombre confuso)
- Fix: lógica de orden duplicado movida a SQL constraint
- Eliminado generate_carnet_zip() (se movió a DMS phase 4)
"""

from odoo import models, fields, api, _


class DocumentRequired(models.Model):
    """Documento requerido para un tipo de trámite."""
    _name = "certprodoo.document.required"
    _description = "Documento Requerido"
    _inherit = ["certprodoo.nomenclator.mixin"]
    _rec_name = "name"
    _order = "procedure_type_id, sequence"

    name = fields.Char(
        string="Nombre",
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string="Descripción",
        tracking=True,
    )
    sequence = fields.Integer(
        string="Orden",
        default=10,
        tracking=True,
        help="Orden de aparición del documento dentro del trámite.",
    )
    procedure_type_id = fields.Many2one(
        "certprodoo.procedure.type",
        string="Tipo de Trámite",
        tracking=True,
        ondelete="cascade",
        help="Tipo de trámite al que aplica este documento requerido. "
             "Vacío = aplica a todos los trámites.",
    )
    is_document_required = fields.Boolean(
        string="Documento Obligatorio",
        default=False,
        tracking=True,
        help="Si está marcado, el documento es obligatorio para el trámite.",
    )
    is_personal_document = fields.Boolean(
        string="Documento Personal",
        default=False,
        tracking=True,
        help="Si está marcado, es un documento personal del solicitante "
             "(ej. CI, Currículum). Se sincroniza globalmente.",
    )

    _sql_constraints = [
        (
            "name_procedure_uniq",
            "unique(name, procedure_type_id, company_id)",
            "Ya existe un documento con ese nombre para este trámite!",
        ),
    ]
