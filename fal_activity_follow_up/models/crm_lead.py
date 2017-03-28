# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class FalActivityFollowUp(models.Model):
    _name = 'fal.activity.follow.up'
    _description = 'Activity Follow Up'
    _order = 'sequence'

    @api.model
    def _get_default_account_analytic_id(self):
        return self.user_id.fal_analytic_account_id and self.user_id.fal_analytic_account_id.id

    @api.multi
    @api.depends('lead_id', 'lead_id.active')
    def _get_archived_status(self):
        for activity_follow_up in self:
            if activity_follow_up.lead_id:
                if activity_follow_up.lead_id.active:
                    activity_follow_up.active = True
                else:
                    activity_follow_up.active = False
            else:
                activity_follow_up.active = True

    # Fields Definition
    name = fields.Char(string='Note')
    activity_id = fields.Many2one('crm.activity', 'Activity')
    user_id = fields.Many2one('res.users', 'Responsible')
    expected_date = fields.Date(string='Expected Date')
    realized_date = fields.Date(string='Realized Date')
    state = fields.Selection([('done', 'Done'), ('not_done', 'Not Done')], default='not_done', string='Status')
    lead_id = fields.Many2one('crm.lead', 'Lead', ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Account Analytic', default=_get_default_account_analytic_id)
    duration = fields.Float(string="Duration")
    active = fields.Boolean(string="Active", compute=_get_archived_status, store=True)
    type = fields.Selection([('crm', 'CRM')], string="Type", default='crm')

    # Methods Definition
    @api.multi
    def set_done(self):
        for activity in self:
            lead = activity.lead_id
            body_html = """<div><b>${object.activity_id.name}</b></div>
                %if object.name:
                <div>${object.name}</div>
                %endif"""
            body_html = self.pool['mail.template'].render_template(self.env.cr, self.env.uid, body_html, 'fal.activity.follow.up', activity.id, context=dict(self._context))
            lead.message_post(body_html, subtype_id=activity.activity_id.subtype_id.id)
            activity.state = 'done'

    @api.multi
    def set_not_done(self):
        self.state = 'not_done'

# end of FalActivityFollowUp()
