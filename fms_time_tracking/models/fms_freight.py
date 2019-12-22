# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, models, fields


class FmsFreight(models.Model):
    _inherit = "fms.freight"

    time_tracking_ids = fields.One2many('fms.time.tracking', 'freight_id',
        string='Expeditions Time Tracking')
    tt_running = fields.Boolean(string="Time Tracking is running",
        compute="_check_is_running", default=False, readonly="True", store=False,
        help="Employee has an activity without check_stop for this expedition")

    # @api.depends('time_tracking_ids')
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

    @api.multi
    def action_check_start(self):
        """
            Check Start: create a new activity record
        """
        if len(self) > 1:
            raise exceptions.UserError(
                _('Cannot perform check start or check stop on multiple employees.'))
        action_date = fields.Datetime.now()
        vals = {
            'freight_id': self.id,
            'employee_id': self.env.user.employee_ids[:1].id,
            'check_start': action_date,
        }
        return self.env['fms.time.tracking'].create(vals)


    @api.multi
    def action_check_stop(self):
        """
            Check Stop: modify check_stop field of appropriate activity record
        """
        if len(self) > 1:
            raise exceptions.UserError(
                _('Cannot perform check star or check stop on multiple employees.'))
        action_date = fields.Datetime.now()
        employee = self.env.user.employee_ids[:1]
        # activity = self.time_tracking_ids.search([
        #     ('employee_id', '=', employee.id),
        #     ('check_stop', '=', False),
        # ], limit=1)
        activity = self.env['fms.time.tracking'].search([
            ('freight_id', '=', self.id),
            ('employee_id', '=', employee.id),
            ('check_stop', '=', False),
        ], limit=1)
        if activity:
            activity.check_stop = action_date
        else:
            raise exceptions.UserError(_('Cannot perform check stop '
                'on %(empl_name)s, could not find corresponding check start. '
                'Your activities have probably been modified manually by '
                'human resources.') % {'empl_name': employee.name,})
        return activity

