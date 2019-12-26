# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, models, fields, _
from odoo.http import request
import httpagentparser, requests, platform


class FmsFreight(models.Model):
    _inherit = "fms.freight"

    time_tracking_ids = fields.One2many('fms.time.tracking', 'freight_id',
        string='Expeditions Time Tracking')
    tt_running = fields.Boolean(string="Time Tracking is running",
        compute="_check_is_running", default=False, readonly="True", store=False,
        help="Employee has an activity without check_stop for this expedition")

    def _check_is_running(self):
        if self.time_tracking_ids:
            vals = {}
            running = self.env['fms.time.tracking'].search([
                ('freight_id', '=', self.id),
                ('employee_id', '=', self.env.user.employee_ids[:1].id),
                ('check_stop', '=', False),
            ], limit=1)
            if running:
                vals.update({'tt_running': True})
            self.update(vals)

    def action_time_check(self, latitude=None,longitude=None):
        """
            Check Start: create a new activity record
            Check Stop: modify check_stop field of appropriate activity record
        """
        if len(self) > 1:
            raise exceptions.UserError(
                _('Cannot perform check start or check stop on multiple employees.'))
        action_date = fields.Datetime.now()
        employee = self.env.user.employee_ids[:1]
        vals = {
            'freight_id': self.id,
            'employee_id': employee.id,
        }

        key = self.env['ir.config_parameter'].sudo().get_param(
                                                'fms_time_tracking.fms_google_api_key')
        if key and latitude and longitude:
            api_response = requests.get(
            'https://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&key=%s' % (
                latitude, longitude, key))
            api_response_dict = api_response.json()
            if api_response_dict['status'] == 'OK':
                location_name = api_response_dict['results'][0]['formatted_address']
            else:
                location_name = api_response_dict['status']
        else:
            location_name = _('It has not been able to establish location')

        if not self.tt_running:
            agent = request.httprequest.environ.get('HTTP_USER_AGENT')
            agent_details = httpagentparser.detect(agent)
            user_os = agent_details.get('name', '')
            if not user_os:
                user_os = agent_details.get('platform', {}).get('name')
            browser_name = agent_details.get('browser', {}).get('name', '')
            bit_type = platform.architecture() or ''
            vals.update({
                'check_start': action_date,
                'location_name_start': location_name,
                'latitude_start': latitude,
                'longitude_start': longitude,
                'os_name': user_os + ", " + bit_type[0],
                'browser_name': browser_name,
            })
            self.env['fms.time.tracking'].create(vals)
            return {'action': 'success'}
        else:
            activity = self.env['fms.time.tracking'].search([
                ('freight_id', '=', self.id),
                ('employee_id', '=', employee.id),
                ('check_stop', '=', False),
            ], limit=1)
            if activity:
                vals.update({
                    'check_stop': action_date,
                    'location_name_stop': location_name,
                    'latitude_stop': latitude,
                    'longitude_stop': longitude,
                })
                activity.update(vals)
                return {'action': 'success'}
            else:
                raise exceptions.UserError(
                    _('Can not perform check stop on %(empl_name)s, could not '
                      'find corresponding check start. Your activities have probably '
                      'been modified manually by human resources.') % {
                                               'empl_name': employee.name, })
                return {'warning': 'fail'}

    @api.multi
    def action_close(self):
        # Check there aren't any time trackin running
        activity = self.env['fms.time.tracking'].search([
            ('freight_id', '=', self.id),
            ('check_stop', '=', False),
        ], limit=1)
        if activity:
            raise exceptions.UserError(
                _('You can not close expedition if there are any activity with time running. '
                  'Be sure to close all activities started before closing expedition.'))

        super(FmsFreight, self).action_close()
