# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, RedirectWarning, ValidationError


import odoo.addons.decimal_precision as dp
import logging
import os

_logger = logging.getLogger(__name__)



class StockCard(models.Model):
	_name 		= "stock.card"
	_rec_name 	= "product_id"
	
	name		= fields.Char(string="Number", default= 'New')
	date_start	= fields.Date(string="Date Start", required=True, default=fields.Date.context_today)
	date_end	= fields.Date("Date End", required=True, default=fields.Date.context_today)
	location_id = fields.Many2one('stock.location', string='Location', required=True)
	product_id	= fields.Many2one('product.product', string='Product', required=True)
	lot_id		= fields.Many2one('stock.production.lot', string='Serial Number', required=False)
	expired_date= fields.Date(string="Expired Date")
	line_ids	= fields.One2many('stock.card.line','stock_card_id',string='Details', ondelete="cascade")
	state		= fields.Selection([('draft','Draft'),('open','Open'), ('done','Done')],string='Status',readonly=True,required=True, default="draft")
	user_id		= fields.Many2one('res.users', string='Created', default=lambda self: self.env.user)
	

# 	_defaults = {
# 		'Date_start'     	: lambda *a : time.strftime("%Y-%m-%d") ,
# 		'Date_end'     		: lambda *a : time.strftime("%Y-%m-%d") ,
# 		'user_id'			: lambda obj, cr, uid, context: uid,
# 		'ref'				: lambda obj, cr, uid, context: '/',		
# 		"state"				: "draft",
# 	}	

	@api.multi
	def action_calculate(self):
		# kosongkan stock_card_line
		# cari stock move product_id dan location_id, start_Date to end_Date
		# insert into stock_card_line
		# jika keluar dari location (source_id) maka isi ke qty_out
		# jika masu ke location (dest_id) maka isi ke qty_in
		# hitung qty_balance = qty_start + qty_in - qty_out 
		# start balance dihitung dari total qty stock move sebelum start_Date

		stock_move = self.env['stock.move']
		stock_card_line = self.env['stock.card.line']
		product = self.env['product.product']

		for sc in self:
			self.env.cr.execute("delete from stock_card_line where stock_card_id=%s" % sc.id)

			qty_start = 0.0
			qty_balance = 0.0
			qty_in = 0.0
			qty_out = 0.0
			product_uom = False
			value_start = 0.0

# 			### cari product_id id moves
# 			lot_id = sc.product_id
# 			print "lot_id", lot_id.id
# 			sql2 = "select move_id from stock_quant_move_rel qm " \
# 					"join stock_quant q on qm.quant_id = q.id "\
# 					"where q.lot_id = %s" % (lot_id.id)
# 			self.env.cr.execute(sql2)
# 			res = self.env.cr.fetchall()
# 			print"msmmsmsmsmms", res
# 			move_ids = []
# 			if res and res[0]!= None:
# 				for move in res:
# 					move_ids.append(move[0])

			## beginning balance in 
# 			sql = "select sum(product_uom_qty) from stock_move where product_id=%s " \
# 				  "and date < '%s' and location_dest_id=%s " \
# 				  "and id in %s" \
# 				  "and state='done'" %(sc.product_id.id, sc.date_start, sc.location_id.id, tuple(move_ids))
			sql = "select sum(product_uom_qty) from stock_move where product_id=%s " \
				  "and date < '%s' and location_dest_id=%s " \
				  "and state='done'" %(sc.product_id.id, sc.date_start, sc.location_id.id)
			
			self.env.cr.execute(sql)
			res = self.env.cr.fetchone()
			if res and res[0]!= None:
				qty_start = res[0]

			## beginning balance out
			sql = "select sum(product_uom_qty) from stock_move where product_id=%s and date < '%s' and location_id=%s and state='done'" %(
				sc.product_id.id, sc.date_start, sc.location_id.id)
			self.env.cr.execute(sql)
			res = self.env.cr.fetchone()
			
			if res and res[0]!= None:
				qty_start = qty_start - res[0]
			
			##begining balance values in
			sql_price = "select sum(price_unit*product_uom_qty)/sum(product_uom_qty) from stock_move where product_id=%s " \
				  "and date < '%s' and location_dest_id=%s " \
				  "and state='done'" %(sc.product_id.id, sc.date_start, sc.location_id.id)
			self.env.cr.execute(sql_price)
			res = self.env.cr.fetchone()
			if res and res[0]!= None:
				value_start = res[0]	  
			
			sql = "select sum(price_unit*product_uom_qty)/sum(product_uom_qty) from stock_move where product_id=%s and date < '%s' and location_id=%s and state='done'" %(
				sc.product_id.id, sc.date_start, sc.location_id.id)
			self.env.cr.execute(sql)
			res = self.env.cr.fetchone()
			
			if res and res[0]!= None:
				value_start = value_start - res[0]
			
			## product uom
			# import pdb;pdb.set_trace()
			prod = product.browse([sc.product_id.id])
			product_uom = prod.uom_id 


			data = {
				"stock_card_id"	: sc.id,
				"date"			: False,
				"qty_start"		: False,
				"qty_in"		: False,
				"qty_out"		: False,
				"qty_balance"	: qty_start,
				"value"			: value_start,	
				"product_uom_id": product_uom.id,
				
			}
			stock_card_line.create(data)

			##mutasi
			sm_ids = stock_move.search([
				'|',
				('location_dest_id','=',sc.location_id.id),
				('location_id','=',sc.location_id.id),
				('product_id', 	'=' , sc.product_id.id),
				('date', 		'>=', sc.date_start),
				('date', 		'<=', sc.date_end),
				('state',		'=',  'done'),
				

			], order='date asc')

			for sm in sm_ids :
				print "==========", sm
				qty_in = 0.0
				qty_out = 0.0
				value_in = value_out = 0.0
				#uom conversion factor
				if product_uom.id != sm.product_uom.id:
					factor =  product_uom.factor / sm.product_uom.factor 
				else:
					factor = 1.0

				if sm.location_dest_id == sc.location_id:	#incoming, dest = location
					qty_in = sm.product_uom_qty  * factor
					value_in = sm.product_uom_qty * sm.price_unit * factor	
				elif sm.location_id == sc.location_id:		#outgoing, source = location
					qty_out = sm.product_uom_qty * factor
					value_out = sm.product_uom_qty * sm.price_unit * factor

				qty_balance = qty_start + qty_in - qty_out
				value = value_start + value_in - value_out
				print "kskskkskskskks", qty_balance
				name = sm.name if sm.name!=prod.display_name else ""
				partner_name = sm.partner_id.name if sm.partner_id else ""
				notes = sm.picking_id.note or ""
				po_no = sm.group_id.name if sm.group_id else ""
				origin = sm.picking_id.origin or ""
				finish_product = ""
				print " origin", origin	
				if "MO" in origin:
					mrp = self.pool.get('mrp.production')
					mo_id = mrp.search([("name","=",origin)])
					mo = mrp.browse(mo_id)
					finish_product = "%s:%s"%(mo[0].product_id.name,mo[0].batch_number) if mo else ""


				data = {
					"stock_card_id"	: sc.id,
					"move_id"		: sm.id,
					"picking_id"	: sm.picking_id.id,
					"date"			: sm.date_expected,
					"qty_start"		: qty_start,
					"qty_in"		: qty_in,
					"qty_out"		: qty_out,
					"qty_balance"	: qty_balance,	
					"product_uom_id": product_uom.id,
					"value"			: value,
					"name"			: "%s/ %s/ %s/ %s/ %s/ %s" % (name,finish_product,partner_name,po_no,notes,origin),
				}
				stock_card_line.create(data)
				qty_start = qty_balance
				value_start = value
				
		return
	
	@api.multi
	def action_draft(self):
		#set to "draft" state
		return self.write({'state':'draft'})
	
	@api.multi
	def action_confirm(self):
		#set to "confirmed" state
		return self.write({'state':'open'})
	
	@api.multi
	def action_done(self):
		#set to "done" state
		return self.write({'state':'done'})

	# @api.multi
	# def create(self,vals):
	# 	if vals.get('name', 'New') == 'New':
	# 		vals['name'] = self.env['ir.sequence'].next_by_code('stock.card')  or 'New'
	# 	new_id = super(StockCard, self).create(vals)
	# 	# return new_id


class StockCardLine(models.Model):
	_name 		= "stock.card.line"
	
	name			=	fields.Char(string="Description")
	stock_card_id	=	fields.Many2one('stock.card', string='Stock Card')
	move_id		=	fields.Many2one('stock.move', string='Stock Move')
	picking_id	=	fields.Many2one('stock.picking', string='Picking')
	date		=	fields.Date(string="Date")
	qty_start	=	fields.Float(string="Start")
	qty_in		=	fields.Float(string="Qty In")
	qty_out		=	fields.Float(string="Qty Out")
	qty_balance	=	fields.Float(string="Balance")
	product_uom_id = fields.Many2one('product.uom', string='UoM')
	value		= fields.Float(string="Value")

