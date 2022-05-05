# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from pytz import timezone


class FmsFreight(models.Model):
    _name = 'fms.freight'
    _description = 'Freight Expedition Management'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'name desc'

    name = fields.Char(string='Reference', index=True,
        readonly=True, copy=False,
        help='The reference that will be used on freight expeditions')
    active = fields.Boolean(string='Active', default=True,
        help="If the active field is set to False, it will allow you to hide"
             " the expedition without removing it.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('partial', 'Partial'),
        ('received', 'Received'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
        ('invoiced', 'Invoiced')],
        default='draft',
        string = 'Expedition State',
        help="Gives the state of the Expedition.")
    currency_id = fields.Many2one('res.currency',
        string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company',
        string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users',
        string='Administrator', required=True,
        default=(lambda self: self.env.user),
        domain=lambda self: [
            ("groups_id", "=", self.env.ref("fms.group_fms_manager").id)])
    partner_id = fields.Many2one('res.partner',
        strin='Customer', required=True, change_default=True)
    partner_center = fields.Char('Center code', size=32, index=True)
    partner_department = fields.Char('Department code', size=32, index=True)
    partner_delivery_note = fields.Char('Delivery note', size=32, index=True)
    partner_order_doc = fields.Char('Order doc.', size=32, index=True)
    partner_sale_doc = fields.Char('Sale doc.', size=32, index=True)
    date_order = fields.Datetime('Date Order',
        required=True, default=fields.Datetime.now)
    tag_ids = fields.Many2many('fms.freight.tags', string='Freight State')
    product_id = fields.Many2one('product.product', string='Product')
    privacy_visibility = fields.Selection([
        ('followers', 'On invitation only'),
        ('employees', 'Visible by all employees'),
        ],
        default='followers', string='Privacy', required=True,
        help="Holds visibility of the expedition:\n "
             "- On invitation only: Employees may only "
             "see the followed expeditions.\n"
             "- Visible by all employees: Employees "
             "may see all expeditions.")
    notes = fields.Text(string='Internal Notes')
    # Delivery addres and contact
    delivery_name = fields.Char(string='Contact Name')
    street = fields.Char(string='Delivery street')
    street2 = fields.Char(string='Delivery street2')
    zip_id = fields.Many2one('res.city.zip', 'ZIP Location')
    zip = fields.Char(string='Delivery zip', change_default=True)
    city_id = fields.Many2one('res.city', string='City of Address')
    city = fields.Char(string='Delivery city')
    state_id = fields.Many2one("res.country.state", string='State',
        ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Delivery Country',
        ondelete='restrict')
    email = fields.Char(string='Delivery email')
    phone = fields.Char(string='Delivery phone')
    mobile = fields.Char(string='Delivery mobile')
    # Freight Information
    fr_desc = fields.Html(string='Freight Description', copy=False,
        sanitize_attributes=True, strip_classes=False, sanitize_style=True)
    fr_packages = fields.Integer(string='Nº Packages')
    fr_value = fields.Monetary(string='Freight value',
        currency_field='currency_id')
    fr_commission = fields.Monetary(string='Commission value',
        currency_field='currency_id')
    fr_commission_percent = fields.Float(string='Commission percent')
    # Freight Delivery
    date_planned = fields.Datetime('Scheduled Date',
        track_visibility="onchange", copy=False,
        help='Date at which the expedition should be delivered')
    responsible_id = fields.Many2one('hr.employee',
        string='Responsible', track_visibility="onchange", copy=False,
        help="Employee which is responsible to do the expedition.")
    # Commission Lines
    commission_line_ids = fields.One2many(
        'fms.freight.commission.line', 'freight_id', string="Commission")
    # Invoicing
    invoice_id = fields.Many2one(comodel_name='account.invoice',
        string='Invoice', copy=False)
    invoicing_order_id = fields.Many2one(comodel_name='fms.invoicing.order',
        string='Invoicing Order', copy=False)

    @api.onchange('fr_value','fr_commission_percent')
    def _calculate_fr_commission_percent(self):
        vals = {}
        if self.fr_value == 0 and self.fr_commission_percent != 0:
            vals.update({'fr_commission': 0.0})
        elif self.fr_commission_percent > 100:
            raise ValidationError(
                _("Commission percent should be less or equal to 100!"))
        else:
            vals.update({
                'fr_commission': self.fr_value * (self.fr_commission_percent / 100)
            })
        self.update(vals)

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id.partner_id not in self.message_partner_ids:
            self._origin.message_subscribe([self.user_id.partner_id.id])

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        vals = {}
        vals.update({'fr_commission_percent': self.partner_id.fms_commission})
        self.update(vals)

    def format_date(self, date):
        # format date following user language
        lang_model = self.env['res.lang']
        lang = lang_model._lang_get(self.env.user.lang)
        date_format = lang.date_format
        return datetime.strftime(
            fields.Date.from_string(date), date_format)

    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref(
            'fms.fms_freight_email_template',
            False,
        )
        compose_form = self.env.ref('mail.email_compose_message_wizard_form',
                                    False)
        ctx = {
            'default_model': 'fms.freight',
            'default_res_id': self.id,
            'default_use_template': bool(template),
            'default_template_id': template and template.id or False,
            'default_composition_mode': 'comment',
        }
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def _compute_access_url(self):
        super(FmsFreight, self)._compute_access_url()
        for expedition in self:
            expedition.access_url = '/my/expeditions/%s' % (expedition.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return  self.state == 'draft' and self.name == False and _('Draft Expedition') or \
                self.state == 'draft' and self.name != False and _('Draft Expedition - %s') % (self.name) or \
                self.state != 'draft' and _('Expedition - %s') % (self.name)

    # ---------------------------
    # Buttons Actions
    # ---------------------------
    @api.multi
    def action_partial(self):
        for freight in self:
            vals = ({
                'state': 'partial'
            })
            if not freight.name:
                vals.update({
                    'name': self.env['ir.sequence'].next_by_code('fms.freight')
                })
            freight.update(vals)
            freight.message_post(
                body=_("<h5><strong>Receive Partial</strong></h5>"))

    @api.multi
    def action_receive(self):
        for freight in self:
            vals = ({
                'state': 'received'
            })
            if not freight.name:
                vals.update({
                    'name': self.env['ir.sequence'].next_by_code('fms.freight')
                })
            freight.update(vals)
            freight.message_post(body=_("<h5><strong>Received</strong></h5>"))

    @api.multi
    def action_confirm(self):
        for freight in self:
            freight.update({
                'state': 'confirmed',
                'tag_ids': [(6, 0, [])],
            })
            freight.message_post(body=_(
                "<h5><strong>Confirmed</strong></h5>"
                "And all expedition tags has been removed too."
            ))

    def action_close(self):
        for freight in self:
            freight.update({'state': 'closed'})
            freight.message_post(body=_("<h5><strong>Closed</strong></h5>"))
            # Add employee commission automatically if not exists
            lines = freight.commission_line_ids.filtered(
                lambda l: l.employee_id.id == freight.responsible_id.id
            )
            if not lines:

                vals = {
                    'freight_id': self.id,
                    'employee_id': freight.responsible_id.id,
                    'date': freight.date_planned.astimezone(timezone(self._context.get('tz'))).date(),
                    'currency_id':  self.currency_id.id,
                }
                new_commission = self.env['fms.freight.commission.line'].new(vals)
                # force compute commission
                new_commission._onchange_employee_id()
                vals = new_commission._convert_to_write(new_commission._cache)
                self.env['fms.freight.commission.line'].sudo().create(vals)

    @api.multi
    def action_reopen(self):
        for freight in self:
            freight.update({'state': 'confirmed'})
            freight.message_post(
                body=_("<h5><strong>Reopen: Closed to confirmed</strong></h5>"))

    @api.multi
    def action_cancel(self):
        for freight in self:
            freight.update({'state': 'cancel'})
            freight.message_post(body=_("<h5><strong>Cancelled</strong></h5>"))

    @api.multi
    def action_cancel_draft(self):
        for freight in self:
            vals = ({
                'state': 'draft',
                'date_planned': False,
                'responsible_id': False,
                'tag_ids': [(6, 0, [])],
            })
            freight.update(vals)
            freight.commission_line_ids.unlink()
            freight.message_post(
                body=_("<h5><strong>Cancel to Draft</strong></h5>"))

    def action_show_order(self):
        action = self.env.ref('fms.fms_invoicing_action')
        result = action.read()[0]
        form_view = self.env.ref('fms.fms_invoicing_form_view')
        result['views'] = [(form_view.id, 'form')]
        result['res_id'] = self.invoicing_order_id.id
        return result

    def action_show_invoice(self):
        action = self.env.ref('account.action_invoice_tree1')
        result = action.read()[0]
        form_view = self.env.ref('account.invoice_form')
        result['views'] = [(form_view.id, 'form')]
        result['res_id'] = self.invoice_id.id
        return result

    # ---------------------------
    # Delivery Address
    # ---------------------------
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

    # ---------------------------
    # CRUD overrides
    # ---------------------------
    @api.model
    def create(self, vals=None):
        res = super(FmsFreight, self).create(vals)
        # Add Responsible selected as follower
        res.message_subscribe(partner_ids=[res.user_id.partner_id.id])
        return res

    @api.multi
    def unlink(self):
        for expedition in self:
            if expedition.state not in ('draft', 'cancel'):
                raise UserError(_(
                    "You can only delete expeditions in state draft or canceled."))
        return super(FmsFreight, self).unlink()

    @api.multi
    def write(self, values):
        for freight in self:
            """If state is 'received' and change field 'date_planed': 
               - Automatically change the state to confirmed
               - Remove freight tags
            """
            if values.get('date_planned') and freight.state == 'received':
                values.update({
                    'state': 'confirmed',
                    'tag_ids': [(6, 0, [])],
                })
                freight.message_post(
                    body=_("The state has been changed automatically to "
                    "<strong>Confirmed</strong> because the "
                    "<strong>date</strong> has been changed in received state.<br>"
                    "And all expedition tags has been removed too."))
            else:
                """Create a message in chatter with the name
                   of the freight tags if they have been changed
                """
                if values.get('tag_ids'):
                    if values['tag_ids'][0][2]:
                        tag_ids = values['tag_ids'][0][2]
                        tags = self.env['fms.freight.tags'].browse(tag_ids)
                        tag_names = ''
                        for tag in tags:
                            tag_names += '<li>' + tag.name + "</li>"
                        message = _("Expedition Tags:\n <ul>%s</ul>" % tag_names)
                        freight.message_post(body=message)

        return super(FmsFreight, self).write(values)

    # ---------------------------
    # Invoicing
    # ---------------------------
    @api.multi
    def _prepare_order_line_vals(self, invoicing_order):
        self.ensure_one()
        assert invoicing_order, 'Missing invoicing order'
        vals = {
            'order_id': invoicing_order.id,
            'partner_id': self.partner_id.id,
            'freight_id': self.id,
            }
        return vals
    @api.multi
    def create_invoicing_order_line_from_expedition(self, invoicing_order):
        vals_list = []
        for iline in self:
            vals_list.append(iline._prepare_order_line_vals(invoicing_order))
        return self.env['fms.invoicing.order.line'].create(vals_list)


class FmsFreightTags(models.Model):
    _name = "fms.freight.tags"
    _description = "Tags in freight expeditions"

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index', default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]
