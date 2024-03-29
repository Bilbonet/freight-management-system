# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    fms_commission = fields.Float(string='Percent of commission',
                                  help='FMS default clients % of commission')
