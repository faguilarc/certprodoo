from . import geo_point_widget

# Registrar el widget en el field_registry
from odoo import registry

# Asegurarse de que el registro exista
if not hasattr(registry, 'field_registry'):
    from odoo.fields import field_registry

    registry.field_registry = field_registry

field_registry.add('geo_point', GeoPointWidget)