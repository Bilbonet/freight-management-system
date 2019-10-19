# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fms_commission = fields.Boolean(default=False,
        string='Use in freights commissions',
        help="If set true, it will allow you to use it "
             "in commissions of the freight")

    @api.onchange('type')
    def _onchange_type_freight_commission(self):
        if self.type != 'service':
            self.fms_commission = False
