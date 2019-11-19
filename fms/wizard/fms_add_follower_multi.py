# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class FmsAddFollowerMulti(models.TransientModel):
    _name = 'fms.add.follower.multi'
    _description = 'Add me as follower'

    @api.multi
    def run(self):
        self.ensure_one()
        assert self._context['active_model'] == 'fms.freight',\
            'Active model should be fms.freight'
        expeditions = self.env['fms.freight'].browse(self._context['active_ids'])
        for expedition in expeditions:
            if self.create_uid.partner_id not in expedition.message_partner_ids:
                expedition.message_subscribe([self.create_uid.partner_id.id])
