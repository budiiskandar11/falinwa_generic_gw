from odoo import models, fields, api


class FalBusinessGroup(models.Model):
    _name = 'fal.business.group'

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company')
    sales_team_id = fields.Many2one('crm.team', string='Sales Team')
    notes   = fields.Text(string="Notes")
    user_id = fields.Many2one('res.users',string="Responsible")
    description = fields.Char(string="Business Field")

class FalCrmGroup(models.Model):
    _name = 'fal.crm.project'

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company')
    notes   = fields.Text(string="Notes")
    user_id = fields.Many2one('res.users',string="Responsible")
    description = fields.Char(string="Business Field")
    sales_team_id = fields.Many2one('crm.team', string='Sales Team')

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    fal_business_group_id = fields.Many2one(
        'fal.business.group', string='Business Group'
    )
    fal_project_group_id = fields.Many2one(
        'fal.crm.project', string='Project'
    )
    currency_id = fields.Many2one('res.currency',string="Currency", default=lambda self: self.env.user.company_id.currency_id.id)

    @api.onchange('fal_business_group_id')
    def fal_onchange_business_group(self):
        if self.fal_business_group_id:
            self.team_id = self.fal_business_group_id.sales_team_id.id
            self.company_id = self.fal_business_group_id.company_id.id
        else:
            self.team_id = False
            self.company_id = False


