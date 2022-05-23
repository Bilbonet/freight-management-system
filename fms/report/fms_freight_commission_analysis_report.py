# Copyright 2022 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import tools
from odoo import models, fields, api
from psycopg2.extensions import AsIs


class FmsFreightCommissionAnalysisReport(models.Model):
    _name = "fms.freight.commission.analysis.report"
    _description = "FMS Freight Commission Analysis Report"
    _auto = False
    _rec_name = 'expedition_id'

    @api.model
    def _get_selection_commission_type(self):
        return self.env['hr.employee'].fields_get(
            allfields=['fms_type'])['fms_type']['selection']

    date_comm = fields.Date(string='Date Commission', readonly=True)
    employee_id = fields.Many2one(string='Employee', 
        comodel_name='hr.employee', readonly=True)
    amount = fields.Float(string='Amount Commission', readonly=True)
    commission_type = fields.Selection(selection='_get_selection_commission_type',
        string="Commision Type", readonly=True)
    expedition_id = fields.Many2one(string='Expedition',
        comodel_name='fms.freight', readonly=True)
    expedition_value = fields.Float(string='Expedition Value', readonly=True)
    value_rest = fields.Float(string='Value - Commission', readonly=True)

    def _select(self):
        select_str = """
            SELECT MIN(fcl.id) AS id,
            fcl.date AS date_comm,
            fcl.employee_id AS employee_id,
            SUM(fcl.amount) AS amount,
            emp.fms_type As commission_type,
            ff.id AS expedition_id,
            SUM(ff.fr_commission) AS expedition_value,
            SUM(ff.fr_commission - fcl.amount) AS value_rest
        """
        return select_str

    def _from(self):
        from_str = """
            fms_freight_commission_line fcl
            LEFT JOIN hr_employee emp ON fcl.employee_id = emp.id
            LEFT JOIN fms_freight ff ON fcl.freight_id = ff.id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
            fcl.date, 
            fcl.employee_id,
            emp.fms_type,
            ff.id
        """
        return group_by_str

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            "CREATE or REPLACE VIEW %s AS ( %s FROM %s %s )", (
                AsIs(self._table),
                AsIs(self._select()),
                AsIs(self._from()),
                AsIs(self._group_by())
            ),
        )
