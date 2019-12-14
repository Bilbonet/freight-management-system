# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class FmsFreight(models.Model):
    _inherit = "fms.freight"

    digital_signature = fields.Binary(string='Digital Signature',
        store=True, attachment=False)
