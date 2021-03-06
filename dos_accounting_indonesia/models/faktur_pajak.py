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
from mx.TextTools.Examples.Python import string
from Carbon.Aliases import false


class FakturPajak(models.Model):
	_name = 'faktur.pajak'
	_description = 'Faktur Pajak Indonesia'

	
	nomor_perusahaan = fields.Char(string='Nomor Perusahaan', size=3,default="010")
	tahun_penerbit = fields.Char(string='Tahun Penerbit', size=2, default=lambda self: fields.Date.from_string(fields.Date.context_today(self)).strftime('%y'))
	kode_cabang = fields.Char(string='Kode Cabang', size=3, default="000")
	nomor_urut = fields.Char(string='Nomor Urut', size=8)
	name = fields.Char(string='Nomor Faktur', compute='_get_faktur',store=True)
	invoice_id = fields.Many2one('account.invoice',string='Invoice No')
	partner_id = fields.Many2one('res.partner', sting="Customer")
	dpp = fields.Monetary(string='Untaxed Amount')
	tax_amount = fields.Monetary(string="Tax Amount")
	date_used = fields.Date(string="Used Date")
	company_id = fields.Many2one('res.company', string='Company')
	currency_id = fields.Many2one('res.currency', string='Currency')
	pajak_type = fields.Selection([('in','Faktur Pajak Masukan'),('out','Faktur Pajak Keluaran')],string='Type',default="out")
	state = fields.Selection([('0','Not Used'),('1','Used'),('2','Reported'),('3','Cancelled')],string='Status', default='0')

	@api.depends('name','nomor_perusahaan','kode_cabang','tahun_penerbit','nomor_urut')
	def _get_faktur(self):
		res = {}
		for nomor in self :
			name = "%s.%s-%s.%s" % (nomor.nomor_perusahaan, nomor.kode_cabang, nomor.tahun_penerbit, nomor.nomor_urut)
			print "mmdmdmmdmmdmdm", name
			nomor.update({'name':name})
	
	@api.multi
	def used(self):
		self.write({'state': '1'})
	
	@api.multi
	def report(self):
		self.write({'state': '2'})
	
	@api.multi
	def cancel(self):
		self.write({'state': '3'})
			