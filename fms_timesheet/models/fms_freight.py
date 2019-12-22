# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class FmsFreight(models.Model):
    _inherit = "fms.freight"

    timesheet_ids = fields.One2many('fms.timesheet', 'freight_id',
        string='Expeditions Timesheets')
