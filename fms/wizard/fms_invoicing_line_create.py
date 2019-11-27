# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class FmsInvoicingOrderLineCreate(models.TransientModel):
    _name = 'fms.invoicing.order.line.create'
    _description = 'Wizard to create order lines'

    order_id = fields.Many2one(
        'fms.invoicing.order', string='Invoicing Order')
    date_planned = fields.Date(string="Scheduled Date")
    partner_center = fields.Char(
        'Center code', size=32)
    partner_department = fields.Char(
        'Department code', size=32)
    product_id = fields.Many2one(
        'product.product', 'Product')
    freight_ids = fields.Many2many(
        'fms.freight', string='Expeditions')

    @api.model
    def default_get(self, field_list):
        res = super(FmsInvoicingOrderLineCreate, self).default_get(field_list)
        context = self.env.context
        assert context.get('active_model') == 'fms.invoicing.order',\
            'active_model should be fms.invoicing.order'
        assert context.get('active_id'), 'Missing active_id in context !'
        order = self.env['fms.invoicing.order'].browse(context['active_id'])
        res.update({
            'order_id': order.id,
            })
        return res

    @api.multi
    def _prepare_expedition_domain(self):
        self.ensure_one()
        domain = [('state', '=', 'closed'),
                  ('partner_id', '=', self.order_id.partner_id.id),
                  ('company_id', '=', self.order_id.company_id.id),
                  ('date_planned', '<=', self.date_planned),]
        if self.partner_center:
            domain += [('partner_center', '=', self.partner_center)]
        if self.partner_department:
            domain += [('partner_department', '=', self.partner_department)]
        if self.product_id:
            domain += [('product_id', '=', self.product_id.id)]

        orderlines = self.env['fms.invoicing.order.line'].search([
            ('state', 'in', ('draft','done')),
            ('freight_id', '!=', False)])
        if orderlines:
            expeditions_ids = [
                orderline.freight_id.id for orderline in orderlines]
            domain += [('id', 'not in', expeditions_ids)]
        return domain

    @api.multi
    def populate(self):
        domain = self._prepare_expedition_domain()
        lines = self.env['fms.freight'].search(domain)
        self.freight_ids = lines
        action = {
            'name': _('Select Expeditions to Create Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'fms.invoicing.order.line.create',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': self._context,
        }
        return action

    @api.onchange(
        'date_planned','partner_center','partner_department','product_id')
    def expedition_filters_change(self):
        domain = self._prepare_expedition_domain()
        res = {'domain': {'freight_ids': domain}}
        return res

    @api.multi
    def create_order_lines(self):
        if self.freight_ids:
            # pass
            self.freight_ids.create_invoicing_order_line_from_expedition(
                self.order_id)
        return True