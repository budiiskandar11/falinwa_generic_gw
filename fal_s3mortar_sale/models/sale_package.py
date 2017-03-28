# -*- coding: utf-8 -*-

import math

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import amount_to_text_en
from odoo.addons.dos_amount_to_text_id import amount_to_text_id
import odoo.addons.decimal_precision as dp

class CrmTeam(models.Model):
    _inherit = "crm.team"

    sale_type = fields.Selection([('project','Project'),
        ('retail',"Retail"),
        ('agen',"Agent"),
        ('package','Package')],string="Sale Type", default="retail")

class SalePackage(models.Model):
    _name = "sale.package"
    _description = "Sale Package for S3Mortar"

    name = fields.Char(string="Package Name")
    partner_id  = fields.Many2one('res.partner',string="Customer")
    team_id     = fields.Many2one('crm.team', string="Type")
    package_price = fields.Float(string="Package Price")
    product_ids = fields.One2many('package.lines','package_id',string="Product Lines")

