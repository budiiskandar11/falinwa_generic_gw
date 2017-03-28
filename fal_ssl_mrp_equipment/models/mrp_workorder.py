from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    
    number = fields.Char(string="Number", default=lambda self: self.env['ir.sequence'].next_by_code('mrp.workorder'))