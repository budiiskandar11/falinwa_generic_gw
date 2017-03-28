from openerp.addons.crm import crm_stage
from openerp.osv import fields, osv
from openerp import tools


class crm_opportunity_report(osv.Model):
    _inherit = "crm.opportunity.report"

    _columns = {
        'fal_lead_sales_person_id': fields.many2one('res.users', 'Lead Salesperson', readonly=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'crm_opportunity_report')
        cr.execute("""
            CREATE OR REPLACE VIEW crm_opportunity_report AS (
                SELECT
                    c.id,
                    c.date_deadline,

                    c.date_open as opening_date,
                    c.date_closed as date_closed,
                    c.date_last_stage_update as date_last_stage_update,

                    c.user_id,
                    c.fal_lead_sales_person_id,
                    c.probability,
                    c.stage_id,
                    stage.name as stage_name,
                    c.type,
                    c.company_id,
                    c.priority,
                    c.team_id,
                    activity.nbr_activities,
                    c.active,
                    c.campaign_id,
                    c.source_id,
                    c.medium_id,
                    c.partner_id,
                    c.country_id,
                    c.planned_revenue as total_revenue,
                    c.planned_revenue*(c.probability/100) as expected_revenue,
                    c.create_date as create_date,
                    extract('epoch' from (c.date_closed-c.create_date))/(3600*24) as  delay_close,
                    abs(extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24)) as  delay_expected,
                    extract('epoch' from (c.date_open-c.create_date))/(3600*24) as  delay_open,
                    c.lost_reason,
                    c.date_conversion as date_conversion
                FROM
                    "crm_lead" c
                LEFT JOIN (
                    SELECT m.res_id, COUNT(*) nbr_activities
                    FROM "mail_message" m
                    WHERE m.model = 'crm.lead'
                    GROUP BY m.res_id ) activity
                ON
                    (activity.res_id = c.id)
                LEFT JOIN "crm_stage" stage
                ON stage.id = c.stage_id
                GROUP BY c.id, activity.nbr_activities, stage.name
            )""")
