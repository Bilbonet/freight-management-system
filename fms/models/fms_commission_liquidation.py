# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class FmsCommissionLiquidation(models.Model):
    _name = 'fms.commission.liquidation'
    _description = 'Commission Liquidation Order'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Name',
        readonly=True, copy=False)
    company_id = fields.Many2one('res.company',
        string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(related='company_id.currency_id',
        store=True, readonly=True)
    active = fields.Boolean(default=True,
        help="If the active field is set to False, it will allow you to hide"
             " the liquidation without removing it.")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancel', 'Canceled'),
        ], string='Status', readonly=True, copy=False, default='draft',
        track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee',
        string='Employee', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        track_visibility="onchange")
    date = fields.Date(string='Liquidation Date',
        required = True, readonly=True, states={'draft': [('readonly', False)]},
        track_visibility="onchange")
    cl_line_ids = fields.One2many('fms.commission.liquidation.line', 'liquidation_id',
        string='Liquidation Lines')
    amount_total = fields.Monetary(compute='_compute_total',
        store=True, readonly=True, currency_field='currency_id')

    _sql_constraints = [(
        'name_company_unique',
        'unique(name, company_id)',
        'A commission line already exists with this reference '
        'in the same company!'
        )]

    @api.multi
    @api.depends('cl_line_ids', 'cl_line_ids.c_amount')
    def _compute_total(self):
        for rec in self:
            rec.amount_total = sum(
                rec.mapped('cl_line_ids.c_amount') or
                [0.0])

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.cl_line_ids:
            raise UserError(_(
                "There are commission lines.\n "
                "Before you change the employee you have to delete all lines."))

    @api.onchange('date')
    def _onchange_date(self):
        if self.cl_line_ids:
            for line in self.cl_line_ids:
                if line.c_date > self.date:
                    raise UserError(_(
                        "There are commission lines with date higher than "
                        "selected date.\n"
                        "Please delete those lines or select a higher date."))

    def _prepare_commission_domain(self):
        self.ensure_one()
        domain = [('employee_id','=', self.employee_id.id),
                  ('state', '=', 'draft'),
                  ('date', '<=', self.date),]

        liquidations = self.env['fms.commission.liquidation.line'].search([
            ('liquidation_id.state', '=', 'draft')])
        if liquidations:
            commission_ids = [
                line.f_commission_id.id for line in liquidations]
            domain += [('id', 'not in', commission_ids)]
        return domain

    def action_populate(self):
        domain = self._prepare_commission_domain()
        lines = self.env['fms.freight.commission.line'].search(domain)
        if lines:
            for line in lines:
                self.env['fms.commission.liquidation.line'].create({
                    'liquidation_id': self.id,
                    'f_commission_id': line.id,
                })
        else:
            raise UserError(_(
                "There aren't any commission pending for this employee and date."))

    def action_confirm(self):
        if self.cl_line_ids:
            vals = {
                'state': 'done',
                'liquidation_order': self.id,
            }
            for line in self.cl_line_ids:
                line.f_commission_id.update(vals)
            self.update({'state': 'done'})
        else:
            raise UserError(_(
                "There aren't any commission line."))

    def action_cancel(self):
        if self.cl_line_ids:
            vals = {
                'state': 'cancel',
            }
            for line in self.cl_line_ids:
                line.f_commission_id.update(vals)
            self.state = 'cancel'
    def cancel2draft(self):
        if self.cl_line_ids:
            vals = {
                'state': 'draft',
                'liquidation_order': False,
            }
            for line in self.cl_line_ids:
                line.f_commission_id.update(vals)
            self.update({'state': 'draft'})

    # ------------------------
    # CRUD overrides
    # ------------------------
    @api.model
    def create(self, vals=None):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fms.commission.liquidation') or 'New'
        return super(FmsCommissionLiquidation, self).create(vals)

    @api.multi
    def unlink(self):
        for liquidation in self:
            if liquidation.state != 'draft':
                raise UserError(_(
                    "You can only delete Liquidation Orders in state draft."))
        return super(FmsCommissionLiquidation, self).unlink()