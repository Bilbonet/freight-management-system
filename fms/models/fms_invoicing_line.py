# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FmsInvoicingOrderLine(models.Model):
    _name = 'fms.invoicing.order.line'
    _description = 'Invoicing Line'

    name = fields.Char(
        string='Order Line Reference', readonly=True, copy=False)
    order_id = fields.Many2one(
        'fms.invoicing.order', string='FMS Invoicing Order',
        ondelete='cascade', index=True)
    company_id = fields.Many2one(
        related='order_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(
        related='order_id.currency_id', store=True, readonly=True)
    state = fields.Selection(
        related='order_id.state', string='State',
        readonly=True, store=True)
    partner_id = fields.Many2one(
        related='order_id.partner_id', store=True, readonly=True)
    freight_id = fields.Many2one(
        'fms.freight', string='Expedition Reference',
        ondelete='restrict')
    f_date_planned = fields.Datetime(
        related='freight_id.date_planned', readonly=True)
    f_product_id = fields.Many2one(
        related='freight_id.product_id', readonly=True)
    f_state = fields.Selection(
        related='freight_id.state', readonly=True)
    amount = fields.Monetary(
        related='freight_id.fr_commission', readonly=True,
        currency_field='currency_id')

    _sql_constraints = [(
        'name_company_unique',
        'unique(name, company_id)',
        'A payment line already exists with this reference '
        'in the same company!'
        )]

    @api.multi
    def _prepare_invoice_line(self):
        self.ensure_one()
        invoice_line_vals = {
            'product_id': self.f_product_id.id,
            'quantity': 1,
            'uom_id': self.f_product_id.uom_id.id,
            'fms_freight_id': self.freight_id.id,
            # 'discount': self.discount,
            # 'contract_line_id': self.id,
        }
        invoice_line = self.env['account.invoice.line'].new(invoice_line_vals)
        # Get other invoice line values from product onchange
        invoice_line._onchange_product_id()
        invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)
        invoice_line_vals.update(
            {
                'name': self.name,
                'price_unit': self.amount,
            }
        )
        return invoice_line_vals

    def _set_expedition_invoiced(self, invoice_id):
        self.ensure_one()
        vals = {
            'invoice_id': invoice_id,
            'state': 'invoiced',
        }
        self.freight_id.update(vals)
    def _set_expedition_closed(self):
        self.ensure_one()
        vals = {
            'invoice_id': False,
            'state': 'closed',
        }
        self.freight_id.update(vals)
    # -----------------------
    # CRUD overrides
    # -----------------------
    @api.model
    def create(self, vals=None):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fms.invoicing.order.line') or 'New'

        return super(FmsInvoicingOrderLine, self).create(vals)
