# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

from openerp import models, fields


class HrAnalyticTimesheet(models.Model):
    _inherit = 'account.analytic.line'

    lead_id = fields.Many2one(string='Lead/Opportunity',
                              comodel_name='crm.lead')
    meeting_id = fields.Many2one(string='Meeting',
                                   comodel_name='calendar.event')
