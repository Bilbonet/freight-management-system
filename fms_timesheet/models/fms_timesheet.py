# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from datetime import datetime, timedelta


class FmsTimesheet(models.Model):
    _name = 'fms.timesheet'
    _description = 'Spent time in freight expeditions'
    _order = 'date_time_start desc, id desc'

    company_id = fields.Many2one('res.company',
        string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    active = fields.Boolean('Active', default=True,
        help="If the active field is set to False, it will allow "
        "you to hide the timesheet without removing it.")
    name = fields.Char(string='Timesheet Title')
    date_time_start = fields.Datetime(string='Start date time',
        default=fields.Datetime.now, required=True)
    date_time_stop = fields.Datetime(string='End date time',
        compute='_get_stop_date_time', store=True)
    amount = fields.Float(string='Quantity', default=0.0)
    employee_id = fields.Many2one('hr.employee',
        string='Employee', required=True)
    freight_id = fields.Many2one('fms.freight',
        string='Freight Expedition', ondelete='cascade', required=True)

    @api.model
    def default_get(self, fields):
        res = super(FmsTimesheet, self).default_get(fields)
        employee =  self._context.get('employee_id')
        res.update({
            'employee_id': employee or False,
        })
        return res

    @api.one
    @api.depends('date_time_start', 'amount')
    def _get_stop_date_time(self):
        for line in self:
            line.date_time_stop = datetime.strptime(
                str(line.date_time_start), "%Y-%m-%d %H:%M:%S"
                ) + timedelta(seconds=line.amount*3600)

    @api.multi
    def button_end_work(self):
        end_date = datetime.now()
        for line in self:
            date = fields.Datetime.from_string(line.date_time_start)
            line.amount = (end_date - date).total_seconds() / 3600
        return True
