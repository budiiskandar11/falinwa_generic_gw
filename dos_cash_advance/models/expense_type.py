# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp

class ExpenseType(models.Model):
    _name = "expense.type"
    _description = "Expense Type"
    
    
    name    = fields.Char(string="Name")
    code    = fields.Char(string='Code')
    account_id = fields.Many2one('account.account', string="Account")