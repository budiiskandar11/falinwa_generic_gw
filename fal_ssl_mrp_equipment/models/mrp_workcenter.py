from dateutil import relativedelta
import datetime

from odoo import api, exceptions, fields, models, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'
    
    workcenter_type = fields.Selection([('routing','Routing'),
        ('machine','Machine')],string="Type")
