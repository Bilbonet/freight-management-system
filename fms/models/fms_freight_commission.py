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

    complete_name = fields.Char(string='Complete Name',
        compute='_compute_complete_name', store=True)
    freight_id = fields.Many2one(string='Expedition', 
        comodel_name='fms.freight',
        ondelete='cascade', required=True)
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
    employee_id = fields.Many2one(string='Employee', 
        comodel_name='hr.employee', required=True)
    # emp_commission: Deprecated
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
        for rec in self:
            rec.complete_name = '(%s) %s / %s' % (
                rec.id, rec.freight_id.name, rec.freight_id.partner_id.name)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Commission calculation:
            With method onchange only calculates commissions with type percent
        """
        if (not self.employee_id.id or 
            self.freight_id.fr_commission == 0):
            # Nothing to calc if not employee or freight commission is 0
            return None

        vals = {}
        amount = 0.0
        if self.employee_id.fms_type == 'percent':
            if self.employee_id.fms_commission != 0:
                amount = self.freight_id.fr_commission * (self.employee_id.fms_commission / 100)
                vals.update({'amount': amount})
                self.update(vals)
            return None

    def create(self, vals):
        """
        Commission calculation: 
            This calculation is only for employees with distribution commission type. 
            Commissions by percent type is calculated in 'onchange' method.
        """

        """
        Creating new distribution commission lines.
        """
        new_distri_lines = self.env['hr.employee'].browse(
                [e['employee_id'] for e in vals]
            ).filtered(
                    lambda e: e.fms_type == 'distribution'
                )
        """
        We look if there are previous distribution commission lines.
        """
        freigth_obj = self.env['fms.freight'].browse(vals[0].get('freight_id'))
        prev_distri_lines = freigth_obj.commission_line_ids.filtered(
                    lambda l: l.employee_id.fms_type == 'distribution'
                )

        if new_distri_lines or prev_distri_lines:
            amount = freigth_obj.fr_commission
            if amount != 0:
                """
                We are creating employees with percent commission?
                We need to discount the amount of commission before to distribute.
                """
                emp_percent = self.env['hr.employee'].browse(
                        [e['employee_id'] for e in vals]
                    ).filtered(
                            lambda e: e.fms_type == 'percent'
                        )              
                if emp_percent:
                    amount_percent = 0
                    for ap in [l for l in vals if l['employee_id'] in emp_percent.ids]:
                        amount_percent = amount_percent + ap.get('amount')

                    if amount_percent != 0:
                        amount = amount - amount_percent

                """
                Exists previous percent commissions?
                We have to discount these too 
                """
                prev_percent_lines = freigth_obj.commission_line_ids.filtered(
                            lambda l: l.employee_id.fms_type == 'percent'
                        )
                if prev_percent_lines:
                    for ppl in prev_percent_lines:
                        amount = amount - ppl.amount 

                """
                We distribute the amount between the new lines and the previous ones
                """
                distri_to = len(prev_distri_lines) + len(new_distri_lines)
                amount = amount / distri_to
                for line in [l for l in vals if l['employee_id'] in new_distri_lines.ids]:
                    line.update({'amount': amount})
                
                # Update previous lines
                for line in prev_distri_lines:
                    line.write({
                        'amount': amount
                    })
        
        return super(FmsFreightCommissionLine, self).create(vals)

    def write(self, vals):
        """
        Commission calculation: 
            When we change any employee we have to recalculate distribution commissions
        """
        res = super(FmsFreightCommissionLine, self).write(vals)

        if 'employee_id' in vals:
            """
            If there is any commission distribution lines, we have to distribute the commission
            """
            distri_lines = self.freight_id.commission_line_ids.filtered(
                lambda l: l.employee_id.fms_type == 'distribution'
            ) 

            if distri_lines and self.freight_id.fr_commission != 0:
                    amount = self.freight_id.fr_commission
                    """
                    Exists lines with percent commissions?
                    We have to discount these 
                    """
                    percent_lines = self.freight_id.commission_line_ids.filtered(
                        lambda l: l.employee_id.fms_type == 'percent'
                    )
                    if percent_lines:
                        for ppl in percent_lines:
                            amount = amount - ppl.amount

                    """
                    We distribute the amount between the distribution commission lines
                    """   
                    amount = amount / len(distri_lines)
                    distri_lines.update({
                        'amount': amount
                    })
        return res

    def unlink(self):
        """
        Commission calculation: 
            When we delete any employee we have to recalculate distribution commissions.
            If there is any commission distribution lines, we have to distribute the commission
        """        
        distri_lines = self.freight_id.commission_line_ids.filtered(
            lambda l: l.employee_id.fms_type == 'distribution' and 
                      l.employee_id != self.employee_id
        )
        if distri_lines and self.freight_id.fr_commission != 0:
                amount = self.freight_id.fr_commission
                """
                Exists lines with percent commissions?
                We have to discount these 
                """
                percent_lines = self.freight_id.commission_line_ids.filtered(
                    lambda l: l.employee_id.fms_type == 'percent' and 
                              l.employee_id != self.employee_id
                )
                if percent_lines:
                    for ppl in percent_lines:
                        amount = amount - ppl.amount

                """
                We distribute the amount between the rest of distribution commission lines
                """   
                amount = amount / len(distri_lines)
                distri_lines.update({
                    'amount': amount
                })

        return super(FmsFreightCommissionLine, self).unlink()