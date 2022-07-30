# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fms_invoicing_order_id = fields.Many2one(
        comodel_name='fms.invoicing.order', 
        string='FMS Invoicing Order',
        copy=False)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    fms_freight_id = fields.Many2one(
        comodel_name='fms.freight', 
        string='Expedition Ref.',
        copy=False)