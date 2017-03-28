from openerp import fields, models, api
from openerp.tools.translate import _


class crm_lead2opportunity_partner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.user_id = self.partner_id.user_id and self.partner_id.user_id.id

# end of crm_lead2opportunity_partner()
