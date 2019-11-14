# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    fms_invoicing = fields.Boolean(default=False,
        string="Expedition invoicing",
        help="If set true, it will allow you to use it "
             "in expedition invoicing")
    fms_commission = fields.Boolean(default=False,
        string="Employee commission",
        help="If set true, it will allow you to use it "
             "in emplyee's commissions in the expeditions")

    @api.onchange('type')
    def _onchange_type_freight_commission(self):
        if self.type != 'service':
            self.fms_invoicing = False
            self.fms_commission = False
