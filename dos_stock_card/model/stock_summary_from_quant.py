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
SC_STATES = [('draft', 'Draft'), ('open', 'Open'), ('done', 'Done')]


class StockSummary(models.Model):
	_name = "stock.summary"
	_rec_name = "location_id"
	
	ref 	= fields.Char(string="Number", default=lambda self: self.env['ir.sequence'].next_by_code('stock.card') or 'New')
	date_start= fields.Date(string="Date Start")
	date_end	= fields.Date(string="Date End")
	location_id	=	fields.Many2one('stock.location', string='Location')
	line_ids	=	fields.One2many( 'stock.summary.line', 'stock_summary_id',string='Details', ondelete="cascade")
	breakdown_sn = fields.Boolean(string="Breakdown Serial Number?")
	state		=	fields.Selection( SC_STATES, string='Status',readonly= True,required=True, default="draft")
	user_id	= 	fields.Many2one('res.users', string='Created', default=lambda self: self.env.user)
	

# 	_defaults = {
# 		'date_start'     	: lambda *a : time.strftime("%Y-%m-%d") ,
# 		'date_end'     		: lambda *a : time.strftime("%Y-%m-%d") ,
# 		'user_id'			: lambda obj,  context: uid,
# 		'ref'				: lambda obj,  context: '/',
# 		"state"				: "draft",
# 	}

	@api.multi
	def action_calculate(self):
		# kosongkan stock_summary_line
		# cari list produk yang ada stocknya di location id
		# cari stock move product_id dan location_id, start_date to end_date
		# insert into stock_summary_line
		# jika keluar dari location (source_id) maka isi ke qty_out
		# jika masu ke location (dest_id) maka isi ke qty_in
		# hitung qty_balance = qty_start + qty_in - qty_out 
		# start balance dihitung dari total qty stock move sebelum start_date

		stock_summary_line = self.env['stock.summary.line']

		for sc in self:
			self.env.self.env.cr.execute("delete from vit_stock_summary_line where stock_summary_id=%s" % sc.id)

			if sc.breakdown_sn:
				self.beginning_lines_sn(stock_summary_line, sc)
				self.mutasi_lines_sn(stock_summary_line, sc)
			else:
				self.beginning_lines_nosn(stock_summary_line, sc)
				self.mutasi_lines_nosn(stock_summary_line, sc)

			self.update_balance(sc)

		return

	@api.multi
	def beginning_lines_sn(self,stock_summary_line, sc):
		line_type = "beg"
		self.process_lines_sn(line_type, stock_summary_line, sc)
	
	@api.multi
	def mutasi_lines_sn(self,stock_summary_line, sc):
		line_type = "mut"
		self.process_lines_sn(line_type,  stock_summary_line, sc)

	@api.multi
	def process_lines_sn(self,line_type,  stock_summary_line, sc):
		sql = "select \
			product_id, \
			uom_id,\
			qty,\
			lot_id, \
			in_date, \
			id \
			from stock_quant where \
			%s and \
			location_id %s"

		##########################################################################
		# fill product
		##########################################################################
		if line_type == "beg":
			self.fill_product_data(sql, stock_summary_line, sc)
			self.update_starting(sql, stock_summary_line, sc)

		return

		##########################################################################
		# update incoming: qty_in
		# outgoing: qty_out
		##########################################################################
		if line_type=="mut":
			self.update_incoming(sql, stock_summary_line, sc)
			self.update_outgoing( sql, stock_summary_line, sc)


		##########################################################################
		# sub total
		##########################################################################




	def fill_product_data(self, sql, stock_summary_line, sc, context=None):
		date  = "in_date <= '%s 24:00:00'"  % (sc.date_end)
		self.env.cr.execute(sql % (date, "=%s" % (sc.location_id.id)))
		res = self.env.cr.fetchall()
		if not res or res[0] == None:
			return False
		for beg in res:
			product_id = beg[0]
			product_uom_id = beg[1]
			lot_id = beg[3] if beg[3] is not None else False
			quant_id = beg[5]

			# cari stock move
			sql3 = "select qm.move_id from \
				stock_quant_move_rel qm \
				left join stock_move m on m.id = qm.move_id \
				where qm.quant_id=%s and \
				(m.location_dest_id=%s or m.location_id=%s)" %(
				quant_id, sc.location_id.id, sc.location_id.id)
			self.env.cr.execute(sql3)
			moves = self.env.cr.fetchall()
			if not moves or moves[0] == None:
				data = {
					"stock_summary_id": sc.id,
					"product_id"	: product_id,
					"product_uom_id"	: product_uom_id,
					"lot_id"			: lot_id,
					"stock_quant_id"	: quant_id,
					"stock_move_id"			: False
				}
				stock_summary_line.create( data)
			else:
				for move in moves:
					move_id = move[0]
					data = {
						"stock_summary_id"	: sc.id,
						"product_id"		: product_id,
						"product_uom_id"	: product_uom_id,
						"lot_id"			: lot_id,
						"stock_quant_id"	: quant_id,
						"stock_move_id"			: move_id
					}
					stock_summary_line.create( data)

	def update_starting(self,  sql, stock_summary_line, sc, context=None):
		date = "write_date < '%s 00:00:00'" % (sc.date_start)
		self.env.cr.execute(sql % (date, "=%s"%(sc.location_id.id)))
		res = self.env.cr.fetchall()
		if not res or res[0] == None:
			return

		for beg in res:
			product_id = beg[0]
			sm_uom_id = beg[1]
			qty = beg[2]
			qty, product_uom_id = self.convert_uom_qty( product_id, sm_uom_id, qty)
			quant_id = beg[5]

			# cari stock move
			sql3 = "select qm.move_id,m.product_uom_qty from stock_quant_move_rel qm \
				left join stock_move m on m.id = qm.move_id \
				where qm.quant_id=%s" % (quant_id)
			self.env.cr.execute(sql3)
			moves = self.env.cr.fetchall()
			if not moves or moves[0] == None:
				sql2 = "update vit_stock_summary_line set \
							qty_start = %s \
							where stock_summary_id=%s and stock_quant_id = %s" % \
					   (qty, sc.id, quant_id)
				self.env.cr.execute(sql2)
			else:
				for move in moves:
					sql2 = "update vit_stock_summary_line set \
								qty_start = %s \
								where stock_summary_id=%s and stock_quant_id = %s and stock_move_id=%s" % \
						   (move[1], sc.id, quant_id, move[0])
					self.env.cr.execute(sql2)

	def update_incoming(self,  sql, stock_summary_line, sc, context=None):
		date = "in_date >= '%s 00:00:00' and in_date <='%s 24:00:00'" % (sc.date_start,sc.date_end)
		self.env.cr.execute(sql % (date, "=%s"%(sc.location_id.id)))
		res = self.env.cr.fetchall()
		if not res or res[0] == 'None':
			return

		for beg in res:
			product_id = beg[0]
			sm_uom_id = beg[1]
			qty = beg[2]
			qty, product_uom_id = self.convert_uom_qty( product_id, sm_uom_id, qty)
			quant_id = beg[5]
			sql2 = "update vit_stock_summary_line set \
						qty_in = %s \
						where stock_summary_id=%s and stock_quant_id = %s" % \
				   (qty, sc.id, quant_id)
			self.env.cr.execute(sql2)

	def update_outgoing(self,  sql, stock_summary_line, sc, context=None):
		date = "in_date >= '%s 00:00:00' and in_date <='%s 24:00:00'" % (sc.date_start,sc.date_end)
		self.env.cr.execute(sql % (date, "<>%s"%(sc.location_id.id)))
		res = self.env.cr.fetchall()
		if not res or res[0] == 'None':
			return

		for beg in res:
			product_id = beg[0]
			sm_uom_id = beg[1]
			qty = beg[2]
			qty, product_uom_id = self.convert_uom_qty( product_id, sm_uom_id, qty)
			quant_id = beg[5]
			sql2 = "update vit_stock_summary_line set \
						qty_out = %s \
						where stock_summary_id=%s and stock_quant_id = %s" % \
				   (qty, sc.id, quant_id)
			self.env.cr.execute(sql2)

	def update_balance(self,  sc, context=None):
		sql3 = "update vit_stock_summary_line set \
			qty_balance =  coalesce( qty_start,0) +  coalesce(qty_in,0) -  coalesce(qty_out,0) \
	    	where stock_summary_id = %s " % (sc.id)
		self.env.cr.execute(sql3)

	def beginning_lines_nosn(self,  stock_summary_line, sc, context=None):
		date = "date < '%s 24:00:00'" % (sc.date_start)
		line_type = "beg"
		self.process_lines_nosn( line_type, date, stock_summary_line, sc)



	def mutasi_lines_nosn(self,  stock_summary_line, sc, context=None):
		date = "date >= '%s 00:00:00' and date <= '%s 24:00:00'" % (sc.date_start, sc.date_end)
		line_type = "mut"
		self.process_lines_nosn( line_type, date,  stock_summary_line, sc)


	def process_lines_nosn(self,line_type, date,  stock_summary_line, sc, context=None):

		sql = "select product_id,\
					product_uom,\
					sum(product_uom_qty) \
					from stock_move as m \
					where %s and %s = %s \
					and state = 'done' \
					group by product_id,product_uom \
					order by product_id"

		# incoming
		self.env.cr.execute(sql % (date, "location_dest_id", sc.location_id.id))
		res = self.env.cr.fetchall()
		if not res or res[0] == 'None':
			return

		if line_type=="beg":
			for beg in res:
				product_id = beg[0]
				sm_uom_id = beg[1]
				qty = beg[2]
				qty,product_uom_id = self.convert_uom_qty( product_id,sm_uom_id,qty )
				data = {
					"stock_summary_id"	: sc.id,
					"product_id"		: product_id,
					"product_uom_id"	: product_uom_id,
					"qty_start"			: qty,
					"qty_in"			: 0,
					"qty_out"			: 0,
					"qty_balance"		: 0,
				}
				stock_summary_line.create( data)
		else:
			for incoming in res:
				product_id = incoming[0]
				sm_uom_id = incoming[1]
				qty = incoming[2]
				qty,product_uom_id = self.convert_uom_qty( product_id,sm_uom_id,qty )

				sql2 = "update vit_stock_summary_line set \
		    	    				qty_in = %s \
		    	    				where stock_summary_id = %s and product_id=%s" % (qty, sc.id, product_id)
				self.env.cr.execute(sql2)


		# outgoing
		self.env.cr.execute(sql % (date, "location_id", sc.location_id.id))
		res = self.env.cr.fetchall()
		if not res or res[0] == 'None':
			return

		if line_type=="beg":
			for beg in res:
				product_id = beg[0]
				sm_uom_id = beg[1]
				qty = beg[2]
				qty,product_uom_id = self.convert_uom_qty( product_id,sm_uom_id,qty )
				sql2 = "update vit_stock_summary_line set \
							qty_start = qty_start - %s \
							where stock_summary_id = %s and product_id=%s" % (
					qty, sc.id ,product_id )
				self.env.cr.execute(sql2)
		else:
			for outgoing in res:
				product_id = outgoing[0]
				sm_uom_id = outgoing[1]
				qty = abs(outgoing[2])
				qty,product_uom_id = self.convert_uom_qty( product_id,sm_uom_id,qty )

				sql2 = "update vit_stock_summary_line set \
							qty_out = %s \
							where stock_summary_id = %s and product_id=%s" % (
					qty, sc.id, product_id)
				self.env.cr.execute(sql2)

		# balance
		sql = "update vit_stock_summary_line set qty_balance = qty_start + qty_in - qty_out \
			where stock_summary_id = %s " % (sc.id)
		self.env.cr.execute(sql)

	def convert_uom_qty(self,  product_id,sm_uom_id,qty,context=None):

		product = self.pool.get('product.product').browse( product_id)
		uom 	= self.pool.get('product.uom').browse( sm_uom_id)

		if product_id == 45:
			print 'ini'
		if uom.id != product.uom_id.id:
			factor = product.uom_id.factor / uom.factor
		else:
			factor = 1.0

		converted_qty = qty * factor

		return converted_qty, product.uom_id.id

	#
	# def beginning_lines_sn(self,  stock_summary_line, sc, context=None):
	#
	# 	date = "in_date < '%s'" % (sc.date_start)
	#
	# 	sql = "select product_id,\
	#     		uom_id,\
	#     		lot_id, \
	#     		qty \
	#     		from stock_quant as q \
	#     	  	where %s and location_id = %s \
	#     		order by product_id" % (
	# 		date, sc.location_id.id)
	# 	self.env.cr.execute(sql)
	#
	# 	res = self.env.cr.fetchall()
	# 	if not res or res[0] == 'None':
	# 		return
	#
	# 	old_product_id = False
	# 	i = 0
	# 	total_start = 0.0
	#
	# 	for beg in res:
	# 		product_id = beg[0]
	#
	#
	# 		### sub total produc
	# 		if old_product_id != product_id and i != 0:
	# 			data = {
	# 				"name"				: "Sub Total %s" % (product_id),
	# 				"stock_summary_id"	: sc.id,
	# 				"product_id"		: False,
	# 				"product_uom_id"	: False,
	# 				"lot_id"			: False,
	# 				"qty_start"			: total_start,
	# 				"qty_in"			: 0,
	# 				"qty_out"			: 0,
	# 				"qty_balance"		: 0,
	# 			}
	# 			stock_summary_line.create( data)
	# 			total_start = 0.0
	#
	# 		data = {
	# 			"stock_summary_id"	: sc.id,
	# 			"product_id"		: product_id,
	# 			"product_uom_id"	: beg[1],
	# 			"lot_id"			: beg[2],
	# 			"qty_start"			: beg[3],
	# 			"qty_in"			: 0,
	# 			"qty_out"			: 0,
	# 			"qty_balance"		: 0,
	# 		}
	# 		stock_summary_line.create( data)
	# 		old_product_id = product_id
	# 		total_start += beg[3]
	# 		i += 1
	#
	# def mutasi_lines_sn(self,  stock_summary_line, sc, context=None):
	# 	date = "in_date >= '%s' and in_date <= '%s'" % (sc.date_start, sc.date_end)
	#
	# 	sql = "select product_id,\
	#     		uom_id,\
	#     		lot_id, \
	#     		qty \
	#     		from stock_quant as q \
	#     	  	where %s and location_id = %s \
	#     		order by product_id" % (
	# 		date, sc.location_id.id)
	# 	self.env.cr.execute(sql)
	#
	# 	res = self.env.cr.fetchall()
	# 	if not res or res[0] == 'None':
	# 		return
	#
	# 	for mut in res:
	# 		product_id = mut[0]
	# 		qty_out = 0.0
	# 		qty_in = 0.0
	# 		if mut[3] < 0:
	# 			qty_out = abs(mut[3])
	# 		else:
	# 			qty_in = mut[3]
	#
	# 		data = {
	# 			"qty_in"		: qty_in,
	# 			"qty_out"		: qty_out,
	# 			"qty_balance"	: 0,
	# 		}
	# 		# line
	# 		sql = "update vit_stock_summary_line set \
	# 			qty_in = %s, qty_out = %s, qty_balance = %s \
	# 			where product_id = %s and stock_summary_id=%s" %(qty_in,qty_out,0,product_id,sc.id)
	# 		self.env.cr.execute(sql)
	#
	# 		#subtotal
	# 		sql = "update vit_stock_summary_line set qty_in"
	#

	def action_draft(self):
		# set to "draft" state
		return self.write({'state' :SC_STATES[0][0]} )

	def action_confirm(self):
		# set to "confirmed" state
		return self.write({'state' :SC_STATES[1][0]} )

	def action_done(self):
		# set to "done" state
		return self.write({'state' :SC_STATES[2][0]} )

	def create(self,  vals, context=None):
		if context is None:
			context = {}
		if vals.get('ref', '/') == '/':
			vals['ref'] = self.pool.get('ir.sequence').get( 'vit.stock_summary') or '/'
		new_id = super(StockSummary, self).create(vals)
		return new_id


class StockSummaryLine(models.Model):
	_name 		= "stock.summary.line"
	_order 		= "product_id"
	
	name		=	fields.Char("Description")
	stock_summary_id	= fields.Many2one('stock.summary', string='Stock Card')
	stock_quant_id	= fields.Many2one('stock.quant', string='Quant')
	product_id	=	fields.Many2one('product.product', string='Product')
	product_uom_id	=	fields.Many2one('product.uom', string='UoM')
	lot_id	=	fields.Many2one('stock.production.lot', string='Serial Number')
	stock_move_id	=	fields.Many2one('stock.move', string='Stock Move')
# 	expired_date	=	fields.Date('lot_id','life_date', type='date',
# 							relation='stock.production.lot',
# 							string='ED',
# 							store=True),
	expired_date 	= fields.Date(string="Expired Date")
	qty_start		= fields.Float(string="Start", digits_compute=dp.get_precision('Product Unit of Measure'))
	qty_in	=	fields.Float(string="Qty In", digits_compute=dp.get_precision('Product Unit of Measure'))
	qty_out = fields.Float(string="Qty Out", digits_compute=dp.get_precision('Product Unit of Measure'))
	qty_balance = fields.Float(string="Balance", digits_compute=dp.get_precision('Product Unit of Measure'))
	

