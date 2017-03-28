# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta, MO
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import odoo.addons.decimal_precision as dp

class ProductWeighting(models.Model):
	_name		='product.weighting'
	_description = 'Product Weighting Record'
	_rec_name = 'partner_id'

	@api.depends('line_ids.total_weight')
	def _compute_amount(self):
		self.total_weight = sum((line.total_weight) for line in self.line_ids)

	name  = fields.Char(string="Number")
	date = fields.Date(string="Date", default=lambda self: fields.Date.from_string(fields.Date.context_today(self)))
	user_id  =  fields.Many2one('res.users', string="Responsible")
	partner_id = fields.Many2one('res.partner', string="Vendor")
	date_start = fields.Date(string="Date Start")
	date_end		= fields.Date(string='Date End')
	total_weight	= fields.Float(string='Total Weight', compute="_compute_amount")
	partner_number = fields.Char(string="Partner No")
	line_ids		= fields.One2many('weighting.lines','weighting_id', string="Weighting Lines")


class WeightingLines(models.Model):
	_name		='weighting.lines'
	_description = "List Truck Weighting"
	_rec_name = 'truck_no'

	@api.depends('weight_in', 'weight_out')
	def _compute_amount(self):
		total_weight=0.0
		for x in self:
			total_weight = x.weight_in - x.weight_out
			x.update({'total_weight':total_weight})

	weighting_id = fields.Many2one('product.weighting', string="Weighting")
	partner_id = fields.Many2one('res.partner', string="Vendor")
	partner_number = fields.Char(string="Partner No")
	product_id = fields.Many2one('product.product',string="Product")
	check_in = fields.Datetime(string="Check In", default=lambda self: fields.Date.from_string(fields.Date.context_today(self)))
	check_out = fields.Datetime(string="Check Out")
	truck_no = fields.Char(string="Truck Licence Plate")
	state		= fields.Selection([('draft','Draft'),('in','Check In'),('out','Check Out'),('done','Done')],string="State", default='draft')
	weight_in	= fields.Float(string="Weight In")
	weight_out	= fields.Float(string="Weight Out")
	total_weight = fields.Float(string="Total Weight", compute='_compute_amount')

	@api.multi
	def propose(self,vals):
		vals['state']='in'
		return self.write(vals)

	@api.multi
	def done(self,vals):
		vals['state']='out'
		return self.write(vals)