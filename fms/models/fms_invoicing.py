# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FmsInvoicingOrder(models.Model):
    _name = 'fms.invoicing.order'
    _description = 'Invoicing Order'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(
        string='Name', readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            self._name
        ),
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id', store=True,
        readonly=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancel', 'Cancel'),
        ], string='Status', readonly=True, copy=False, default='draft',
        track_visibility='onchange')
    partner_id = fields.Many2one('res.partner',
        string='Customer', required=True,
        readonly=True, states={'draft': [('readonly', False)]}, )
    journal_id = fields.Many2one('account.journal',
        string='Journal', required=True, ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda s: s._default_journal(),
        domain="[('type', '=', 'sale'),"
        "('company_id', '=', company_id)]",
        track_visibility='onchange', index=True)
    date_invoice = fields.Date(
        string='Invoice Date', readonly=True,
        states={'draft': [('readonly', False)]}, track_visibility='onchange')
    order_line_ids = fields.One2many(
        'fms.invoicing.order.line', 'order_id', string='Order Lines',
        readonly=True, states={'draft': [('readonly', False)]})
    amount_total = fields.Monetary(
        compute='_compute_total', store=True, readonly=True,
        currency_field='currency_id')
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', copy=False)

    @api.model
    def _default_journal(self):
        company_id = self.env.context.get(
            'company_id', self.env.user.company_id.id
        )
        domain = [
            ('type', '=', 'sale'),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    @api.multi
    @api.depends('order_line_ids', 'order_line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.amount_total = sum(
                rec.mapped('order_line_ids.amount') or
                [0.0])

    # ------------------------
    # CRUD overrides
    # ------------------------
    @api.model
    def create(self, vals=None):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fms.invoicing.order') or 'New'

        return super(FmsInvoicingOrder, self).create(vals)
    @api.multi
    def unlink(self):
        for order in self:
            if order.state != 'cancel':
                raise UserError(_(
                    "You cannot delete an order invoiced. You can "
                    "delete de invoice and then cancel it in order to do so."))
        return super(FmsInvoicingOrder, self).unlink()

    # ------------------------
    # Action Buttons
    # ------------------------
    def create_invoice(self):
        invoice_values = self._prepare_invoice_values()
        return self._finalize_and_create_invoice(invoice_values)
    def action_show_invoice(self):
        action = self.env.ref('account.action_invoice_tree1')
        result = action.read()[0]
        form_view = self.env.ref('account.invoice_form')
        result['views'] = [(form_view.id, 'form')]
        result['res_id'] = self.invoice_id.id
        return result
    @api.multi
    def action_cancel(self):
        for order in self:
            if order.invoice_id:
                raise UserError(_(
                    "You cannot cancel an order with invoice. You can "
                    "delete the invoice and then cancel it."))
            order.write({'state': 'cancel'})
            # Update Expeditions
            for order_line in order.order_line_ids:
                order_line._set_expedition_closed()

        return True
    @api.multi
    def cancel2draft(self):
        self.write({'state': 'draft'})
        return True
    # ------------------------
    # Create Invoice
    # ------------------------
    def _prepare_invoice(self):
        self.ensure_one()
        if not self.journal_id:
            raise ValidationError(
                _("Please define a journal for the company '%s'.")
                % (self.company_id.name or '')
            )

        return {
            'type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'date_invoice': self.date_invoice,
            'journal_id': self.journal_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'fiscal_position_id': self.partner_id.property_account_position_id.id,
            'payment_term_id': self.partner_id.property_payment_term_id.id,
            'user_id': self.partner_id.user_id.id,
            'fms_invoicing_order_id': self.id,
        }
    def _get_lines_to_invoice(self):
        """
        This method fetches and returns the lines to invoice on the order.
        :return: order lines (fms.invoicing.order.line recordset)
        """
        self.ensure_one()
        order_lines = self.order_line_ids
        for line in order_lines:
            if line.f_state != 'closed':
                raise ValidationError(
                    _("The line '%s' is not in state Closed:\n"
                      "All expeditions must be in Closed state "
                      "before invoicing")
                    % (line.name or '')
                )
            if not line.f_product_id:
                raise ValidationError(
                    _("The line '%s' has not a product for invoicing:\n"
                      "All expeditions must have a product before invoicing.")
                    % (line.name or '')
                )

        return order_lines
    def _prepare_invoice_values(self):
        order_lines = self._get_lines_to_invoice()
        if not order_lines:
            raise UserError(_(
                "No valid lines found for invoicing."
                "Please review the order lines."))

        invoice_values = self._prepare_invoice()
        for line in order_lines:
            invoice_values.setdefault('invoice_line_ids', [])
            invoice_line_values = line._prepare_invoice_line()
            if invoice_line_values:
                invoice_values['invoice_line_ids'].append(
                    (0, 0, invoice_line_values)
                )
        return invoice_values

    @api.model
    def _finalize_invoice_values(self, invoice_values):
        """
        This method adds the missing values in the invoice lines dictionaries.

        If no account on the product, the invoice lines account is
        taken from the invoice's journal in _onchange_product_id
        This code is not in finalize_creation_from_contract because it's
        not possible to create an invoice line with no account

        :param invoice_values: dictionary (invoice values)
        :return: updated dictionary (invoice values)
        """
        # If no account on the product, the invoice lines account is
        # taken from the invoice's journal in _onchange_product_id
        # This code is not in finalize_creation_from_contract because it's
        # not possible to create an invoice line with no account
        new_invoice = self.env['account.invoice'].new(invoice_values)
        for invoice_line in new_invoice.invoice_line_ids:
            name = invoice_line.name
            price_unit = invoice_line.price_unit
            invoice_line.invoice_id = new_invoice
            invoice_line._onchange_product_id()
            invoice_line.update(
                {
                    'name': name,
                    'price_unit': price_unit,
                }
            )
        return new_invoice._convert_to_write(new_invoice._cache)
    @api.model
    def _finalize_invoice_creation(self, invoice):
        payment_term = invoice.payment_term_id
        fiscal_position = invoice.fiscal_position_id
        invoice._onchange_partner_id()
        invoice.payment_term_id = payment_term
        invoice.fiscal_position_id = fiscal_position
        invoice.compute_taxes()
    @api.model
    def _finalize_and_create_invoice(self, invoice_values):
        """
        This method:
         - finalizes the invoice values (onchange's...)
         - creates the invoice
         - finalizes the created invoice (onchange's, tax computation...)
        :param invoice_values: Dictionary with (invoice values)
        :return: created invoice (account.invoice)
        """
        if isinstance(invoice_values, dict):
            final_invoice_values = self._finalize_invoice_values(invoice_values)

        invoice = self.env['account.invoice'].create(final_invoice_values)
        self._finalize_invoice_creation(invoice)

        # Update order invoice
        vals = {
            'invoice_id': invoice.id,
            'state': 'done',
        }
        self.update(vals)

        # Update Expeditions
        for order_line in self.order_line_ids:
           order_line._set_expedition_invoiced(invoice.id)

        return invoice




