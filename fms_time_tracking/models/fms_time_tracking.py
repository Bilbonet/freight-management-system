# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, exceptions, fields, models, _


class FmsTimeTracking(models.Model):
    _name = "fms.time.tracking"
    _description = "Expedition Time Tracking"
    _order = "check_start desc"

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    freight_id = fields.Many2one('fms.freight',
        string='Freight Expedition', ondelete='cascade', required=True)
    employee_id = fields.Many2one('hr.employee',
        string="Employee", default=_default_employee,
        required=True, ondelete='cascade', index=True)
    check_start = fields.Datetime(string="Check Start",
        default=fields.Datetime.now, required=True)
    check_stop = fields.Datetime(string="Check Stop")
    worked_hours = fields.Float(string='Worked Hours',
        compute='_compute_worked_hours', store=True, readonly=True)
    # Location
    location_name_start = fields.Char(string="Location Name Start", readonly=True)
    latitude_start = fields.Char(string="Latitude Start", readonly=True)
    longitude_start = fields.Char(string="Longitude Start", readonly=True)
    os_name = fields.Char(string="Operating System", readonly=True)
    browser_name = fields.Char(string="Browser", readonly=True)
    location_name_stop = fields.Char(string="Location Name Stop", readonly=True)
    latitude_stop = fields.Char(string="Latitude Stop", readonly=True)
    longitude_stop = fields.Char(string="Longitude Stop", readonly=True)

    @api.depends('check_start', 'check_stop')
    def _compute_worked_hours(self):
        for activity in self:
            if activity.check_stop:
                delta = activity.check_stop - activity.check_start
                activity.worked_hours = delta.total_seconds() / 3600.0

    @api.constrains('check_start', 'check_stop')
    def _check_validity_check_start_check_stop(self):
        """ verifies if check_start is earlier than check_stop. """
        for activity in self:
            if activity.check_start and activity.check_stop:
                if activity.check_stop < activity.check_start:
                    raise exceptions.ValidationError(
                        _('"Check Stop" time cannot be earlier '
                          'than "Check start" time.'))

    @api.constrains('check_start', 'check_stop', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the activity record compared to the others
            from the same employee.
            For the same employee we must have :
                * maximum 1 "open" activity record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for activity in self:
            # we take the latest attendance before our check_start time and check it
            # doesn't overlap with ours
            last_activity_before_check_start = self.env['fms.time.tracking'].search([
                ('freight_id', '=', activity.freight_id.id),
                ('employee_id', '=', activity.employee_id.id),
                ('check_start', '<=', activity.check_start),
                ('id', '!=', activity.id),
            ], order='check_start desc', limit=1)

            if last_activity_before_check_start \
                and last_activity_before_check_start.check_stop \
                and last_activity_before_check_start.check_stop > activity.check_start:
                raise exceptions.ValidationError(
                    _("Cannot create new activity record for %(empl_name)s, "
                      "the employee was already checked in on %(datetime)s") % {
                    'empl_name': activity.employee_id.name,
                    'datetime': fields.Datetime.to_string(
                        fields.Datetime.context_timestamp(
                            self, fields.Datetime.from_string(activity.check_start))),
                })

            if not activity.check_stop:
                # if our activity is "running" (no check_out), we verify there is no other "running" activity
                no_check_stop_activities = self.env['fms.time.tracking'].search([
                    ('freight_id', '=', activity.freight_id.id),
                    ('employee_id', '=', activity.employee_id.id),
                    ('check_stop', '=', False),
                    ('id', '!=', activity.id),
                ], order='check_start desc', limit=1)
                if no_check_stop_activities:
                    raise exceptions.ValidationError(_("Cannot create new activity record for %(empl_name)s, the employee hasn't checked stop since %(datetime)s") % {
                        'empl_name': activity.employee_id.name,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(no_check_stop_activities.check_start))),
                    })
            else:
                # we verify that the latest activity with check_start time before our check_stop time
                # is the same as the one before our check_start time computed before, otherwise it overlaps
                last_activity_before_check_stop = self.env['fms.time.tracking'].search([
                    ('freight_id', '=', activity.freight_id.id),
                    ('employee_id', '=', activity.employee_id.id),
                    ('check_start', '<', activity.check_stop),
                    ('id', '!=', activity.id),
                ], order='check_start desc', limit=1)
                if last_activity_before_check_stop and last_activity_before_check_start != last_activity_before_check_stop:
                    raise exceptions.ValidationError(_("Cannot create new activity record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        'empl_name': activity.employee_id.name,
                        'datetime': fields.Datetime.to_string(fields.Datetime.context_timestamp(self, fields.Datetime.from_string(last_activity_before_check_stop.check_start))),
                    })

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self):
        raise exceptions.UserError(_('You cannot duplicate an time track activity.'))

