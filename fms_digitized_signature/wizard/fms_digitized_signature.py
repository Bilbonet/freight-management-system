# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class FmsDigitizedSignatureWizard(models.TransientModel):
    _name = "fms.digitized.signature.wizard"
    _description = 'Wizard Delivery Contact Digitized Signature'

    freight_id = fields.Many2one('fms.freight', string='Freight Expedition')
    digital_signature = fields.Binary(string='Digital Signature', attachment=False)

    @api.model
    def default_get(self, field_list):
        res = super(FmsDigitizedSignatureWizard, self).default_get( field_list)
        expedition = self.env['fms.freight'].browse(self._context['active_id'])
        res.update({
            'freight_id': expedition.id,
            })
        if expedition.digital_signature:
            res.update({
                'digital_signature': expedition.digital_signature,
                })
        return res

    @api.multi
    def save(self):
        self.ensure_one()
        assert self._context['active_model'] == 'fms.freight',\
            'Active model should be fms.freight'
        self.freight_id.digital_signature = self.digital_signature
