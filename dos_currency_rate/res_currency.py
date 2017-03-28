# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import math
import re
import time

from odoo import api, fields, models, tools, _

CURRENCY_DISPLAY_PATTERN = re.compile(r'(\w+)\s*(?:\((.*)\))?')


class Currency(models.Model):
    _inherit = "res.currency"
    
    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        
        from_currency = from_currency.with_env(self.env)
        to_currency = to_currency.with_env(self.env)
       
        return from_currency.rate / to_currency.rate