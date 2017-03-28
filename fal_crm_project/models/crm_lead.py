# -*- coding: utf-8 -*-
from openerp import models, fields, api, _, SUPERUSER_ID
from openerp.exceptions import UserError


class crm_lead(models.Model):
    _inherit = "crm.lead"

    @api.multi
    @api.depends("partner_id")
    def _is_customer_have_contact(self):
        for record in self:
            # record.fal_new_admin_contact = False
            record.fal_new_technical_contact = False
            record.fal_is_customer_have_contact = False
            if record.partner_id and record.partner_id.child_ids:
                record.fal_is_customer_have_contact = True

    # Fields Definition
    fal_expertise_skill_tags_ids = fields.Many2many('fal.expertise.skill.tag', 'fal_expertise_skill_tag_rel', 'lead_id', 'tag_id', string="Expertise Skill Tags", domain=[('parent_id', '!=', False), ('child_ids', '=', False)])
    fal_technical_contact = fields.Many2one('res.partner', 'Technical Contact')
    fal_new_technical_contact = fields.Char('New Technical Contact')
    fal_referred_partner = fields.Many2one('res.partner', 'Referred by')
    # fal_responsible_id = fields.Many2one('res.users', 'Customer Project Responsible')
    fal_activity_follow_up_ids = fields.One2many('fal.activity.follow.up', 'lead_id', 'Activity Follow Up')
    fal_admin_contact = fields.Many2one('res.partner', 'Admin Contact')
    # fal_new_admin_contact = fields.Char('New Admin Contact')
    fal_is_customer_have_contact = fields.Boolean('Is Customer Have Contact', compute='_is_customer_have_contact')
    fal_gross_margin = fields.Float(string='Gross Margin')
    fal_net_margin = fields.Float(string='Net Margin')
    fal_lead_sales_person_id = fields.Many2one('res.users', 'Lead Salesperson')
    fal_lead_expertise_tag_line_ids = fields.One2many('fal.lead.expertise.skill.tag.line', 'crm_lead_id', 'Lead Expertise Tag Line')
    fal_project_ids = fields.One2many('project.project', 'fal_origin_lead_id', 'Project List')
    fal_code = fields.Char(string="Code", related='stage_id.fal_code')
    fal_crm_project_team_ids = fields.One2many('fal.crm.project.team', 'lead_id', 'Team')
    fal_from_form = fields.Char("From form")

    # Methods Definition
    @api.multi
    def action_start_qualification(self):
        '''
        This method only change Lead states (stage_id) from New to In Qualification only.
        Nothing to do beside that. Also, it's run by 'Start Qualification' button.
        '''
        stage_id = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_stage_in_qualification').id
        self.write({'stage_id': stage_id})

    @api.multi
    def action_cancel(self):
        for lead in self:
            if lead.type == 'opportunity':
                active_quotation = self.env['sale.order'].search([('opportunity_id', '=', lead.id), ('state', '!=', 'cancel')])
                if not active_quotation:
                    stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_cancelled')
                    stage_id = stage.id
                    lead.write({'stage_id': stage_id})
                else:
                    raise UserError(_('You cannot cancel a customer project with quotation not canceled or not lost'))
            else:
                raise UserError(_('Only Customer Project can be cancelled!'))

    @api.multi
    def action_prepare_technical_meeting(self):
        for lead in self:
            stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_technical_meeting')
            stage_id = stage.id
            lead.write({'stage_id': stage_id})

    @api.multi
    def action_make_appointment(self):
        for lead in self:
            stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_to_quote')
            stage_id = stage.id
            lead.write({'stage_id': stage_id})

    @api.multi
    def action_send_offer(self):
        for lead in self:
            stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_offer_sent')
            stage_id = stage.id
            lead.write({'stage_id': stage_id})

    @api.multi
    def action_make_offer(self):
        for lead in self:
            stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_offer_made')
            stage_id = stage.id
            lead.write({'stage_id': stage_id})

    @api.multi
    def action_get_customer_agreement(self):
        for lead in self:
            stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_customer_agreement')
            stage_id = stage.id
            lead.write({'stage_id': stage_id})

    @api.multi
    def action_cancelled_opportunity(self):
        for lead in self:
            stage = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_cancelled')
            stage_id = stage.id
            lead.write({'stage_id': stage_id})

    @api.multi
    def action_create_partner_and_lost(self):
        '''
        This method doing this:
        1. Convert Lead to Opportunity
        2. Create Customer (res.partner)
        3. Mark an opportunity as Lost
        '''
        for lead in self:
            ctx = dict(self._context)
            partner_id = lead.partner_id and lead.partner_id.id or False
            user_id = lead.user_id and lead.user_id.id or False
            team_id = lead.team_id and lead.team_id.id or False

            # Convert Lead to Opportunity
            lead.convert_opportunity(partner_id, [user_id], team_id)

            # Create customer with flag action = 'create'
            lead.handle_partner_assignation('create', partner_id)

            # mark as lost
            lead.action_set_lost()
            return self.redirect_opportunity_view(lead.id, context=ctx)

    @api.model
    def create(self, vals):
        # Previous development: Create Expertise skill tag.
        if vals.get('fal_expertise_skill_tags_ids', False):
            temp = []

            for fal_expertise_skill_tags_id in self.env['fal.expertise.skill.tag'].browse(vals['fal_expertise_skill_tags_ids'][0][2]):
                temp.append((0, 0, {
                    'expertise_skill_tag_id': fal_expertise_skill_tags_id.id,
                    'company_id': fal_expertise_skill_tags_id.company_id.id,
                    'responsible_id': fal_expertise_skill_tags_id.responsible_id.id,
                    'project_template_id': fal_expertise_skill_tags_id.project_template_id.id,
                }))
            vals['fal_lead_expertise_tag_line_ids'] = temp

        # Call super to create new lead
        res = super(crm_lead, self).create(vals)

        # Recondition for lead coming from survey
        context = dict(self._context or {})
        website_id = context.get('website_id', False)

        if website_id:
            template_id = self.env['ir.model.data'].get_object_reference('fal_crm_project', 'email_template_survey_form_question')
            if 'fal_from_form' in vals:
                if vals['fal_from_form'] == "question":
                    template_id = self.env['ir.model.data'].get_object_reference('fal_crm_project', 'email_template_survey_form_question')
                elif vals['fal_from_form'] == "survey":
                    template_id = self.env['ir.model.data'].get_object_reference('fal_crm_project', 'email_template_survey_form')
            self.env['mail.template'].browse(template_id[1]).send_mail(res.id, force_send=True)
            add_vals = {}
            email = vals.get('email_from', False)
            if email:
                partner_ids = self.env['res.partner'].search([('email', '=', email)], limit=1)
                if partner_ids:
                    partner_id = partner_ids[0]
                    add_vals['partner_id'] = partner_id.id
                    add_vals.update(self.on_change_partner_id(partner_id.id).get('value', {}))
                else:
                    pass
            team_id = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_hotline_sales_team').id
            stage_id = self.stage_find([], team_id, [('fold', '=', False)])
            fal_lead_sales_person_id = self.env['crm.team'].browse(team_id).user_id.id or SUPERUSER_ID
            add_vals.update({'user_id': False, 'team_id': team_id, 'stage_id': stage_id, 'fal_lead_sales_person_id': fal_lead_sales_person_id})
            res.write(add_vals)
        return res

    def on_change_partner_id(self, cr, uid, ids, partner_id, context=None):
        res = super(crm_lead, self).on_change_partner_id(cr, uid, ids, partner_id, context=context)
        value = res.get('value', {})
        value.pop('contact_name', None)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            value['fal_lead_sales_person_id'] = partner.user_id and partner.user_id.id or False
            value['user_id'] = partner.user_id and partner.user_id.id or False
            value['fal_admin_contact'] = False
            value['fal_technical_contact'] = False
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.fal_admin_contact = False
            self.fal_technical_contact = False

    @api.onchange('fal_admin_contact')
    def onchange_fal_admin_contact(self):
        if self.fal_admin_contact:
            self.contact_name = self.fal_admin_contact.name

    @api.onchange('fal_technical_contact')
    def onchange_fal_technical_contact(self):
        if self.fal_technical_contact:
            self.fal_new_technical_contact = self.fal_technical_contact.name

    @api.multi
    def convert_opportunity(self, partner_id, user_ids=False, team_id=False):
        res = super(crm_lead, self).convert_opportunity(partner_id, user_ids, team_id)
        analytic_obj = self.env['account.analytic.account']
        parent_id = analytic_obj.search([('code', '=', 'AFF')], limit=1)[0]
        for lead in self:
            analytic_data = {
                'name': lead.name or '',
                'account_type': 'view',
                'parent_id': parent_id.id,
                'partner_id': lead.partner_id.id,
                'company_id': lead.company_id.id,
            }
            analytic_id = analytic_obj.create(analytic_data)
            for expertise_skill_tag_line in lead.fal_lead_expertise_tag_line_ids:
                project_id = expertise_skill_tag_line.sudo().project_template_id.copy(default={
                    'fal_origin_lead_id': lead.id,
                    'name': lead.name + ' - ' + expertise_skill_tag_line.expertise_skill_tag_id.name,
                    'fal_project_template_id': expertise_skill_tag_line.expertise_skill_tag_id.project_template_id.id,
                    'company_id': expertise_skill_tag_line.company_id.id,
                    'state': 'draft',
                    'code': self.env['ir.sequence'].next_by_code('project.project.level.3.analytic'),
                    'account_type': 'view',
                    'parent_id': analytic_id.id,
                    'fal_is_affaire': True  # it's level 3, should be marked as affaire
                })
                project_id.task_ids.write({
                    'company_id': project_id.company_id.id,
                })
                count_name = 1
                for child_project in project_id.fal_project_template_id.child_ids:
                    if child_project.fal_is_chiffrage:
                        str_count = str(count_name)
                        if count_name < 10:
                            str_count = '0' + str_count
                        project_duplicate_id = self.env['project.project'].sudo().search([('analytic_account_id', '=', child_project.id)]).copy(default={
                            'name': child_project.name,
                            'fal_origin_lead_id': project_id.fal_origin_lead_id.id,
                            'fal_project_template_id': project_id.fal_project_template_id.id,
                            'state': 'draft',
                            'company_id': project_id.company_id.id,
                            'code': project_id.analytic_account_id.code + '_' + str_count,
                            'account_type': 'normal',
                            'parent_id': project_id.analytic_account_id.id,
                            'use_tasks': True,
                            'fal_is_phase': True
                        })
                        if project_duplicate_id:
                            project_duplicate_id.task_ids.write({
                                'company_id': project_id.company_id.id,
                            })
                            count_name += 1
        return res

    @api.multi
    def action_goto_offre(self):
        chiffrage = self.fal_project_ids.filtered(lambda x: x.fal_is_chiffrage)
        if not chiffrage:
            raise UserError(_('This Leads doesnt have Chiffrage Project!'))
        return {
                'name': 'Offre List',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'project.project',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'domain': "[('id', 'in'," + str(chiffrage.ids)+")]",
            }

    def _lead_create_contact(self, cr, uid, lead, name, is_company, parent_id=False, context=None):
        if lead.fal_admin_contact:
            return False
        return super(crm_lead, self)._lead_create_contact(cr, uid, lead, name, is_company, parent_id, context=context)

    def _create_lead_partner(self, cr, uid, lead, context=None):
        partner_obj = self.pool.get('res.partner')
        res = super(crm_lead, self)._create_lead_partner(cr, uid, lead, context=context)
        partner_id = partner_obj.browse(cr, uid, res, context)
        if partner_id.parent_id and not partner_id.is_company:
            res = partner_id.parent_id.id
        return res

    def handle_partner_assignation(self, cr, uid, ids, action='create', partner_id=False, context=None):
        res = super(crm_lead, self).handle_partner_assignation(cr, uid, ids, action, partner_id, context=context)
        lead_obj = self.browse(cr, uid, ids)
        partner_obj = self.pool.get("res.partner")
        new_admin_contact = False
        new_technical_contact = False

        # if many2one contact is filled run this
        if res[ids[0]] != self.browse(cr, uid, ids).fal_admin_contact.id:
            if self.browse(cr, uid, ids).fal_admin_contact:
                self.pool.get("res.partner").write(cr, uid, self.browse(cr, uid, ids).fal_admin_contact.id, {'parent_id': res[ids[0]]})
                new_admin_contact = self.browse(cr, uid, ids).fal_admin_contact.id
        if self.browse(cr, uid, ids).fal_technical_contact:
            self.pool.get("res.partner").write(cr, uid, self.browse(cr, uid, ids).fal_technical_contact.id, {'parent_id': res[ids[0]]})
            new_technical_contact = self.browse(cr, uid, ids).fal_technical_contact.id
        # if not many2one contact filled run this
        if lead_obj.contact_name and not lead_obj.fal_admin_contact:
            new_admin_contact_ids = partner_obj.search(cr, uid, [('name', '=', lead_obj.contact_name), ('parent_id', '=', res[ids[0]])])
            new_admin_contact = new_admin_contact_ids and new_admin_contact_ids[0]
            if not lead_obj.partner_name:
                new_admin_contact = res[ids[0]]
        if lead_obj.fal_new_technical_contact and not lead_obj.fal_technical_contact:
            new_technical_contact = partner_obj.create(cr, uid, {'name': self.browse(cr, uid, ids).fal_new_technical_contact, 'parent_id': res[ids[0]]})

        self.write(cr, uid, ids, {'fal_admin_contact': new_admin_contact, 'fal_technical_contact': new_technical_contact})

        return res

# end of crm_lead()


class fal_expertise_skill_tag(models.Model):
    _name = 'fal.expertise.skill.tag'
    _description = 'Expertise Skill Tag'
    _order = 'sequence'

    parent_id = fields.Many2one('fal.expertise.skill.tag', 'Parent')
    child_ids = fields.One2many('fal.expertise.skill.tag', 'parent_id', 'Childs')
    name = fields.Char(string='Name', index=True, required=True, translate=True)
    company_id = fields.Many2one('res.company', 'Company')
    responsible_id = fields.Many2one('res.users', 'Responsible')
    project_template_id = fields.Many2one('project.project', 'Project Template')
    sustainable_building = fields.Boolean('Is Suistainable Building')
    sequence = fields.Integer(default=10, required=True)
    fal_offer_category_tags_ids = fields.Many2many('fal.offer.category.tag', 'fal_offer_category_expertiseskill_tag_rel', 'expertise_skill_tag__id', 'tag_id', string="Offer Category Tags")

# end of fal_expertise_skill_tag()


class crm_team(models.Model):
    _inherit = 'crm.team'

    def _get_default_team_id(self, cr, uid, context=None, user_id=None):
        if context is None:
            context = {}
        if user_id is None:
            user_id = uid
        team_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'fal_crm_project.fal_classic_sales_team')
        context = dict(context)
        context['default_team_id'] = team_id
        return super(crm_team, self)._get_default_team_id(cr, uid, context=context, user_id=user_id)

# end of crm_team()


class fal_offer_category_tag(models.Model):
    _name = 'fal.offer.category.tag'
    _description = 'Offer Category Tag'
    _order = 'sequence'

    name = fields.Char(string='Name', index=True, required=True, translate=True)
    responsible_id = fields.Many2one('res.users', 'Responsible')
    parent_id = fields.Many2one('fal.offer.category.tag', 'Parent')
    child_ids = fields.One2many('fal.offer.category.tag', 'parent_id', 'Child Tag')
    expertise_skill_tag_ids = fields.Many2many('fal.expertise.skill.tag', 'fal_offer_category_expertiseskill_tag_rel', 'tag_id', 'expertise_skill_tag__id',  string="Expertise Skill Tags")
    sequence = fields.Integer(string='Sequence', default=10)

# end of fal_offer_category_tag()


class fal_lead_expertise_tag_line(models.Model):
    _name = 'fal.lead.expertise.skill.tag.line'
    _description = 'Lead Expertise Skill Tag Line'
    _rec_name = 'expertise_skill_tag_id'

    expertise_skill_tag_id = fields.Many2one('fal.expertise.skill.tag', string='Expertise Skill Tag', required=True, domain="[('parent_id', '!=', False), ('child_ids', '=', False)]")
    company_id = fields.Many2one('res.company', 'Company', required=False)
    responsible_id = fields.Many2one('res.users', 'Responsible')
    project_template_id = fields.Many2one('project.project', 'Project Template')
    crm_lead_id = fields.Many2one('crm.lead', 'Lead', ondelete='cascade')
    fal_customer_project_type_id = fields.Many2one('fal.customer.project.type', related='crm_lead_id.fal_customer_project_type_id')
    partner_id = fields.Many2one('res.partner', related='crm_lead_id.partner_id')
    type = fields.Selection(related='crm_lead_id.type')
    stage_id = fields.Many2one('crm.stage', related='crm_lead_id.stage_id')
    fal_offer_category_tags_ids = fields.Many2many('fal.offer.category.tag', 'fal_offer_category_tag_line_rel', 'expertise_tag_line_id', 'tag_id', string="Offer Category Tags")
    is_lead_active = fields.Boolean("Lead Active", related="crm_lead_id.active")

    @api.onchange('expertise_skill_tag_id')
    def onchange_expertise_skill_tag_id(self):
        if self.expertise_skill_tag_id:
            self.company_id = self.expertise_skill_tag_id.company_id and self.expertise_skill_tag_id.company_id.id or False
        for categorytags in self.fal_offer_category_tags_ids:
            if categorytags.expertise_skill_tag_ids not in self.expertise_skill_tag_id:
                self.fal_offer_category_tags_ids = [(5,)]

# end of fal_lead_expertise_tag_line()


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    fal_code = fields.Char(string="Code")

# end of CrmStage()


class fal_crm_project_team(models.Model):
    _name = 'fal.crm.project.team'

    lead_id = fields.Many2one('crm.lead', 'Lead')
    type = fields.Selection([('cam', 'Team CAM'), ('competitior', 'Competitor')],
        'Type', invisible=True, default='cam')
    type_id = fields.Many2one('fal.crm.project.team.type', 'Type', required=True)
    partner_ids = fields.Many2many('res.partner', 'fal_crmprojectteam_partner_rel', 'crm_project_team_id', 'partner_id', string="Member")
    comment = fields.Text("Comment")
    price = fields.Float("Price")
    uom_id = fields.Many2one('product.uom', "UOM")
    type_id_is_cam = fields.Boolean("Is Type CAM", related="type_id.is_cam")

# end of fal_crm_project_team


class fal_crm_project_team_type(models.Model):
    _name = 'fal.crm.project.team.type'

    name = fields.Char("Name", required=True)
    is_cam = fields.Boolean("Is Type CAM")

# end of fal_crm_project_team_type


class ResUsers(models.Model):
    _inherit = "res.users"

    fal_analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', company_dependent=1)

# end of ResUsers()


class FalActivityFollowUp(models.Model):
    _inherit = 'fal.activity.follow.up'

    @api.multi
    @api.depends('lead_id', 'lead_id.stage_id')
    def _get_lead_active_status(self):
        for activity_follow_up in self:
            cancelled_stage_id = self.env['ir.model.data'].xmlid_to_object('fal_crm_project.fal_cancelled').id
            if activity_follow_up.lead_id.stage_id.id == cancelled_stage_id or activity_follow_up.lead_id.stage_id.fal_is_stage_won:
                activity_follow_up.is_lead_won_lost_canceled = True
            else:
                activity_follow_up.is_lead_won_lost_canceled = False

    # Fields Definition
    is_lead_won_lost_canceled = fields.Boolean('Lead/Opportuinty is Active', compute=_get_lead_active_status, store=True)

# end of FalActivityFollowUp()
