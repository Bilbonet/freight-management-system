# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class FmsCommissionLiquidationLine(models.Model):
    _name = 'fms.commission.liquidation.line'
    _description = 'Commission Liquidation Order Line'
    _order = 'id desc'

    liquidation_id = fields.Many2one('fms.commission.liquidation',
        string='Commission Liquidation Order',
        readonly=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='liquidation_id.company_id',
        store=True, readonly=True)
    currency_id = fields.Many2one(related='liquidation_id.currency_id',
        store=True, readonly=True)
    employee_id = fields.Many2one(related='liquidation_id.employee_id',
        string='Liquidation Order Employee', readonly=True)
    f_commission_id = fields.Many2one('fms.freight.commission.line',
        string='Expedition Commission Line', ondelete='restrict')
    c_freight_id = fields.Many2one(related='f_commission_id.freight_id',
        string='Expedition', readonly=True, ondelete='restrict')
    c_partner_id = fields.Many2one(related='f_commission_id.freight_id.partner_id',
        string='Customer', readonly=True)
    c_delivery_name = fields.Char(related='f_commission_id.freight_id.delivery_name',
        string='Contact Name', readonly=True)
    c_date = fields.Date(related='f_commission_id.date',
        string='Commission Date', readonly=True)
    c_product_id = fields.Many2one(related='f_commission_id.commission_product_id',
        string='Commission Product', readonly=True)
    c_state = fields.Selection(related='f_commission_id.state',
        string='Commission State', readonly=True)
    c_amount = fields.Monetary(related='f_commission_id.amount',
        string='Amount Commission', readonly=True, currency_field='currency_id')
