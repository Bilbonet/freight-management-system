# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class Employee(models.Model):
    _inherit = "hr.employee"

    fms_type = fields.Selection(
        string="FMS Commision Type",
        selection=[
            ('percent', 'Percent'),
            ('distribution', 'Distribution'),
        ],
        default='percent',
        help=(
            'How the commission amount is calculated:\n'
            'Percent: Is a percent of the amount set in (Commission value) of the expedition.\n'
            'Dsitribution: The amount set in (Commission value) is distributed between the commission lines.'
        ),
    )
    fms_commission = fields.Float(string='Percent of commission', default=0.0)
