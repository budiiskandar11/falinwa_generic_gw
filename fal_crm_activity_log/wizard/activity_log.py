# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, fields, models, tools, _


class ActivityLog(models.TransientModel):

    _inherit = "crm.activity.log"

    @api.multi
    def action_log(self):
        print "xxxx, kesini ngga" 
        activ_log = self.env['fal.crm.activity.log']
        for log in self:
            body_html = "<div><b>%(title)s</b>: %(next_activity)s</div>%(description)s%(note)s" % {
                'title': _('Activity Done'),
                'next_activity': log.next_activity_id.name,
                'description': log.title_action and '<p><em>%s</em></p>' % log.title_action or '',
                'note': log.note or '',
            }
            log.lead_id.message_post(body_html, subject=log.title_action, subtype_id=log.next_activity_id.subtype_id.id)
            log.lead_id.write({
                'date_deadline': log.date_deadline,
                'planned_revenue': log.planned_revenue,
                'title_action': False,
                'date_action': False,
                'next_activity_id': False,
            })
            vals = {
                    'name' : log.title_action,
                    'lead_id':log.lead_id.id,
                    'date' : fields.Datetime.now(),
                    'partner_id':log.lead_id.partner_id.id or False,
                    'activity_type_id' : log.next_activity_id.id,
                    'user_id':log.lead_id.user_id.id or False,
                    'team_id': log.lead_id.team_id.id or False,
                    'business_group_id': log.lead_id.fal_business_group_id.id or False,
                    'company_id': log.lead_id.company_id.id or False,
                    'description': log.note or '',


                    }

            activ_log.create(vals)

        return True