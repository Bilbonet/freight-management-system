# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class FmsFreight(models.Model):
    _name = 'fms.freight'
    _description = 'Freight Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char()
    active = fields.Boolean(default=True,
        help="If the active field is set to False, it will allow you to hide"
             " the freight without removing it.")
    state = fields.Selection([
        ('draft', 'Pending'),
        ('partial', 'Partial'),
        ('received', 'Received'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled')],
        string = 'Freight State', readonly=True,
        help="Gives the state of the Freight.",
        default='draft')
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one(
        'res.users', 'Administrator', required=True,
        default=(lambda self: self.env.user),
        domain=lambda self: [
            ("groups_id", "=", self.env.ref("fms.group_fms_manager").id)])
    partner_id = fields.Many2one(
        'res.partner',
        'Customer', required=True, change_default=True)
    partner_center = fields.Char(
        'Center code', size=32, index=True)
    partner_department = fields.Char(
        'Department code', size=32, index=True)
    partner_delivery_note = fields.Char(
        'Delivery note', size=32, index=True)
    partner_order_doc = fields.Char(
        'Order doc.', size=32, index=True)
    partner_sale_doc = fields.Char(
        'Sale doc.', size=32, index=True)
    date_order = fields.Datetime(
        'Date', required=True,
        default=fields.Datetime.now)
    privacy_visibility = fields.Selection([
        ('followers', 'On invitation only'),
        ('employees', 'Visible by all employees'),
    ],
        string='Privacy', required=True,
        default='followers',
        help="Holds visibility of the freight:\n "
             "- On invitation only: Employees may only "
             "see the followed freights.\n"
             "- Visible by all employees: Employees "
             "may see all freights.")
    # Delivery addres and contact
    delivery_name = fields.Char(string='Contact Name')
    street = fields.Char()
    street2 = fields.Char()
    zip_id = fields.Many2one('res.city.zip', 'ZIP Location')
    zip = fields.Char(change_default=True)
    city_id = fields.Many2one('res.city', string='City of Address')
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State',
        ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country',
        ondelete='restrict')
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    # Freight Information
    fr_desc = fields.Html(string='Freight Description',
                               sanitize_attributes=True,
                               strip_classes=False,
                               sanitize_style=True)
    fr_packages = fields.Integer(string='Nº Packages')
    fr_value = fields.Monetary(string='Freight value')
    fr_commission = fields.Monetary(string='Value of commission')
    fr_commission_percent = fields.Float(string='Percent of commission')
    # Freight Delivery
    date_planned = fields.Datetime('Scheduled Date',
        help='Date at which the freight should be delivered')
    responsible_id = fields.Many2one('res.users', string='Responsible')
    # Commission Lines
    commission_line_ids = fields.One2many(
        'fms.freight.commission.line', 'freight_id', string="Commission")

    @api.onchange('fr_commission_percent')
    def _calculate_fr_commission_percent(self):
        if self.fr_value == 0 and self.fr_commission_percent != 0:
            raise ValidationError(
                _("The value of the freight should be different to 0"))
        elif self.fr_commission_percent > 100:
            raise ValidationError(
                _("Commission percent should be less or equal to 100!"))
        else:
            self.fr_commission = self.fr_value * (
                                self.fr_commission_percent / 100)

    @api.onchange('fr_value')
    def _calculate_fr_value(self):
        if self.fr_commission_percent != 0:
            self.fr_commission = self.fr_value * (
                                self.fr_commission_percent / 100)

    # ------------------------------------------------
    # Buttons Actions
    # ------------------------------------------------
    @api.multi
    def action_cancel(self):
        for freight in self:
            freight.state = 'cancel'
            freight.message_post(body=_("<h5><strong>Cancelled</strong></h5>"))

    @api.multi
    def action_cancel_draft(self):
        for freight in self:
            freight.message_post(
                body=_("<h5><strong>Cancel to Draft</strong></h5>"))
            freight.state = 'draft'

    @api.multi
    def action_partial(self):
        for freight in self:
            freight.state = 'partial'
            self.message_post(
                body=_("<h5><strong>Receive Partial</strong></h5>"))

    @api.multi
    def action_receive(self):
        for freight in self:
            freight.state = 'received'
            self.message_post(body=_("<h5><strong>Received</strong></h5>"))

    @api.multi
    def action_confirm(self):
        for freight in self:
            freight.state = 'confirmed'
            self.message_post(body=_("<h5><strong>Confirmed</strong></h5>"))

    @api.multi
    def action_close(self):
        for freight in self:
            freight.state = 'closed'
            self.message_post(body=_("<h5><strong>Closed</strong></h5>"))

    @api.multi
    def action_reopen(self):
        for freight in self:
            freight.state = 'confirmed'
            self.message_post(
                body=_("<h5><strong>Reopen: Closed to confirmed</strong></h5>"))

    # ------------------------------------------------
    # Delivery Address
    # ------------------------------------------------
    @api.onchange('city_id')
    def _onchange_city_id(self):
        if not self.zip_id:
            super()._onchange_city_id()
        if self.zip_id and self.city_id != self.zip_id.city_id:
            self.update({
                'zip_id': False,
                'zip': False,
                'city': False,
            })
        if self.city_id:
            return {
                'domain': {
                    'zip_id': [('city_id', '=', self.city_id.id)]
                },
            }
        return {'domain': {'zip_id': []}}
    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False
        if self.zip_id and self.zip_id.city_id.country_id != self.country_id:
            self.zip_id = False
    @api.onchange('zip_id')
    def _onchange_zip_id(self):
        if self.zip_id:
            vals = {
                'city_id': self.zip_id.city_id,
                'zip': self.zip_id.name,
                'city': self.zip_id.city_id.name,
            }
            if self.zip_id.city_id.country_id:
                vals.update({'country_id': self.zip_id.city_id.country_id})
            if self.zip_id.city_id.state_id:
                vals.update({'state_id': self.zip_id.city_id.state_id})
            self.update(vals)
    @api.constrains('zip_id', 'country_id', 'city_id', 'state_id')
    def _check_zip(self):
        if self.env.context.get('skip_check_zip'):
            return
        for rec in self:
            if not rec.zip_id:
                continue
            if rec.zip_id.city_id.state_id != rec.state_id:
                raise ValidationError(_(
                    "The state of the delivery %s differs from that in "
                    "location %s") % (rec.name, rec.zip_id.name))
            if rec.zip_id.city_id.country_id != rec.country_id:
                raise ValidationError(_(
                    "The country of the delivery %s differs from that in "
                    "location %s") % (rec.name, rec.zip_id.name))
    @api.onchange('state_id')
    def _onchange_state_id(self):
        vals = {}
        if self.state_id.country_id:
            vals.update({'country_id': self.state_id.country_id})
        if self.zip_id and self.state_id != self.zip_id.city_id.state_id:
            vals.update({
                'zip_id': False,
                'zip': False,
                'city': False,
            })
        self.update(vals)

    # ------------------------------------------------
    # CRUD overrides
    # ------------------------------------------------
    @api.model
    def create(self, vals=None):
        # Assign name by sequence
        vals['name'] = self.env['ir.sequence'].next_by_code('fms.freight')

        return super(FmsFreight, self).create(vals)

class FmsFreightCommissionLine(models.Model):
    _name = 'fms.freight.commission.line'
    _description = 'Freight Commission Line'
    _order = 'sequence, id desc'

    freight_id = fields.Many2one(
        'fms.freight', 'freight',
        ondelete='cascade', required=True)
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of"
        " commission order lines.", default=10)
    date = fields.Date(
        'Date', required=True,
        default=fields.Date.context_today)
    user_id = fields.Many2one(
        'res.users', 'User', required=True)
    product_id = fields.Many2one(
        'product.product', 'Product', required=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary(string='Amount Commission')
