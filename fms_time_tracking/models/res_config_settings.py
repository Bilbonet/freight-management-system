# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fms_google_api_key = fields.Char(string='Google Map API KEY')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(fms_google_api_key=self.env['ir.config_parameter'].sudo().get_param(
            'fms_time_tracking.fms_google_api_key'))
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'fms_time_tracking.fms_google_api_key', self.fms_google_api_key)
