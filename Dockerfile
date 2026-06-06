#========================================================================
#  Dockerfile template to modify an image having another image as a base 
#========================================================================

FROM library/library/odoo:14

RUN mkdir -p /mnt/extra-addons/

COPY --chown=odoo:root . /mnt/extra-addons/

USER odoo