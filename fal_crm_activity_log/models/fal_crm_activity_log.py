from odoo import models, fields, api


class FalCrmActivityLog(models.Model):
    _name = 'fal.crm.activity.log'

    name = fields.Char('Summary')
    partner_id = fields.Many2one('res.partner', string="Customer")
    date = fields.Datetime('Date')
    activity_type_id = fields.Many2one('crm.activity',string='Activity Type')
    lead_id = fields.Many2one('crm.lead', string='Leads/Opportunity')
    user_id = fields.Many2one('res.users', string="Salesperson")
    team_id = fields.Many2one('crm.team', string="Sales Team")
    business_group_id = fields.Many2one('fal.business.group', string="Business Group")
    company_id = fields.Many2one('res.company', string="Company")
    description = fields.Text(string="Description")