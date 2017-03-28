# -*- coding: utf-8 -*-
from openerp import api, fields, models


class account_analytic_account(models.Model):
    _inherit = "account.analytic.account"

    fal_is_chiffrage = fields.Boolean('Is Chiffrage?')
    fal_is_affaire = fields.Boolean('Is Affaire?')
    fal_lead_ids = fields.One2many('crm.lead', 'analytic_account_id', string='Opportunity')
    fal_old_code = fields.Char(string="Old Ref.")
    fal_is_phase = fields.Boolean('Is Phase?')

    @api.multi
    def name_get(self):
        res = super(account_analytic_account, self).name_get()
        res_dict = {}
        for item in res:
            res_dict[item[0]] = item[1]
        new_res = []
        for analytic in self.browse(res_dict.keys()):
            grandparent = analytic.parent_id and analytic.parent_id.parent_id and analytic.parent_id.parent_id.name or False
            if analytic.fal_is_phase:
                if analytic.code:
                    name = analytic.code + ' - ' + analytic.name
                    if grandparent:
                        name = analytic.code + ' - ' + grandparent + ' - ' + analytic.name
                else:
                    name = analytic.name
                    if grandparent:
                        name = grandparent + ' - ' + analytic.name
                new_res.append((analytic.id, name))
            else:
                new_res.append((analytic.id, res_dict.get(analytic.id)))
        return new_res

# end of account_analytic_account()


class project(models.Model):
    _inherit = "project.project"

    # Fields Definition
    state = fields.Selection(selection_add=[('draft', 'Offre'), ('pending', 'Pre-affaire')])
    fal_project_template_id = fields.Many2one('project.project', 'Project Template')
    fal_origin_lead_id = fields.Many2one('crm.lead', 'Origin Lead')
    fal_level_4_hide_flag = fields.Boolean(compute='_get_hide_flag', string='Button Hide')
    # fal_is_chiffrage = fields.Boolean('Is Chiffrage?')

    @api.depends('parent_id', 'parent_id.fal_is_affaire', 'fal_is_phase')
    def _get_hide_flag(self):
        for project in self:
            parent = self.sudo().search([('analytic_account_id', '=', project.parent_id.id)])
            if project.fal_is_phase and project.parent_id.fal_is_affaire and parent.state in ['draft', 'pending', 'cancelled', 'close']:
                project.fal_level_4_hide_flag = True
            else:
                project.fal_level_4_hide_flag = False

    @api.multi
    def action_set_preaffaire(self):
        for project in self:
            for child_project in project.fal_project_template_id.child_ids:
                if not child_project.fal_is_chiffrage:
                    project_duplicate_id = self.env['project.project'].sudo().search([('analytic_account_id', '=', child_project.id)]).copy(default={
                        'name': child_project.name,
                        'fal_origin_lead_id': project.fal_origin_lead_id.id,
                        'fal_project_template_id': project.fal_project_template_id.id,
                        'parent_id': project.analytic_account_id.id,
                        'state': 'pending',
                        'company_id': project.company_id.id,
                    })
                    if project_duplicate_id:
                        project_duplicate_id.task_ids.write({
                            'company_id': project.company_id.id,
                        })

            project.write({
                'state': 'pending',
            })

    @api.multi
    def action_set_open(self):
        self.update({'state': 'open'})

    @api.multi
    def action_set_close(self):
        for project in self:
            if project.fal_is_affaire:
                childs = [x.id for x in project.child_ids]
                projects = self.sudo().search([('analytic_account_id', 'in', childs)])
                projects.write({'state': 'close'})
        self.update({'state': 'close'})

    @api.multi
    def action_set_draft(self):
        for project in self:
            if project.fal_is_affaire:
                childs = [x.id for x in project.child_ids]
                projects = self.sudo().search([('analytic_account_id', 'in', childs)])
                projects.write({'state': 'draft'})
        self.update({'state': 'draft'})

    @api.multi
    def action_set_cancelled(self):
        self.update({'state': 'cancelled'})

# end of project()


class task(models.Model):
    _inherit = "project.task"

# end of task()
