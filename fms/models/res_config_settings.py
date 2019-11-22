# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_product_id = fields.Many2one(
        'product.product',string="Expedition Default Product",
        domain="[('fms_invoicing', '=', True)]",
        default_model='fms.freight')
    default_commission_product_id = fields.Many2one(
        'product.product',string="Commission Default Product",
        domain="[('fms_commission', '=', True)]",
        default_model='fms.freight.commission.line')