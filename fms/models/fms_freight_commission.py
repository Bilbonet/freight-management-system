# Copyright 2022 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models, _
from datetime import datetime
import pytz


class FmsFreightCommissionLine(models.Model):
    _name = 'fms.freight.commission.line'
    _description = 'Freight Commission Line'
    _order = 'date, sequence, id desc'
    _rec_name = 'complete_name'

    complete_name = fields.Char('Complete Name',
        compute='_compute_complete_name', store=True)
    freight_id = fields.Many2one('fms.freight',
        string='Expedition', ondelete='cascade', required=True)
    state = fields.Selection([
        ('draft', 'Pending'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),],
        string = 'Commission State',
        readonly=True, default='draft',
        help="Gives the state of the Commission.",)
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of"
        " commission order lines.", default=10)
    date = fields.Date(string='Commission Date', required=True)
    employee_id = fields.Many2one('hr.employee',
        string='Employee', required=True)
    emp_commission = fields.Float(string='Employee % commission',
        related='employee_id.fms_commission', store=False, readonly=True,
        compute_sudo=True)
    commission_product_id = fields.Many2one('product.product',
        string='Commission Product', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary(string='Amount Commission',
        currency_field='currency_id')
    liquidation_order = fields.Many2one('fms.commission.liquidation',
        string='Liquidation Order', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(FmsFreightCommissionLine, self).default_get(fields)
        date = self._context.get('date_planned')

        if date:
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            date = datetime.strftime(pytz.utc.localize(datetime.strptime(date,
            "%Y-%m-%d %H:%M:%S")).astimezone(local),"%Y-%m-%d %H:%M:%S")
        else:
            date = datetime.now()

        res.update({
            'date': date,
        })
        return res

    @api.depends('freight_id.partner_id')
    def _compute_complete_name(self):
        for name in self:
            name.complete_name = '(%s) %s / %s' % (
                name.id, name.freight_id.name, name.freight_id.partner_id.name)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        vals = {}


        if self.freight_id.fr_commission != 0 and self.emp_commission != 0:
            amount = self.freight_id.fr_commission * (self.emp_commission / 100)
            vals.update({'amount': amount})
        self.update(vals)
    
