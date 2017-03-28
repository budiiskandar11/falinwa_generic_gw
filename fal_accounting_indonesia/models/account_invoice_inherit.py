# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice')
    def _compute_amount(self):
    	self.gross = sum((line.price_unit*line.quantity) for line in self.invoice_line_ids)
    	self.disc_total = sum((line.price_unit*line.quantity*line.discount/100) for line in self.invoice_line_ids)
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign


    npwp = fields.Char(string="NPWP")
    gross = fields.Monetary(string='Gross Total',
        store=True, readonly=True, compute='_compute_amount')
    disc_total = fields.Monetary(string='Discount',
        store=True, readonly=True, compute='_compute_amount')
    nomor_faktur_pajak = fields.Char(string='Nomor Faktur Pajak',size=16)
    faktur_pajak = fields.Many2one('faktur.pajak', string="Faktur Pajak")
    invoice_receipt_date = fields.Date('Date Invoice Receipt')
    paid_date   = fields.Date(string="Paid Date")
    due_age = fields.Float(string="Due Age", compute="set_age")

    @api.onchange('partner_id')
    def _onchange_customer_id(self):
        if self.partner_id:
            self.npwp = self.partner_id.npwp or False
            
    @api.multi
    def action_create_faktur(self):
        faktur_obj = self.env['faktur.pajak']
        date = fields.Date.context_today(self)
        
        for inv in self :
            if inv.type == 'out_invoice':
                vals ={
                    'date_used' :date,
                    'invoice_id' :inv.id,
                    'partner_id':inv.partner_id.id,
                    'pajak_type' : 'out',
                    'dpp' : inv.amount_untaxed or 0.0,
                    'tax_amount' :inv.amount_tax or 0.0,
                    'currency_id': inv.currency_id.id,
                    'state' : '1',
                    }
                inv.faktur_pajak.write(vals)
            if inv.type == 'in_invoice' :
                if inv.nomor_faktur_pajak :
                    kode_pt = inv.nomor_faktur_pajak[:3]
                    tahun = inv.nomor_faktur_pajak[4:6]
                    nomor_fp = inv.nomor_faktur_pajak[-8:]
                    print "xxxxxxxxxxxxxxxx", kode_pt, tahun, nomor_fp
                    vals ={
                        'date_used' :date,
                        'invoice_id' :inv.id,
                        'partner_id':inv.partner_id.id,
                        'pajak_type' : 'in',
                        'dpp' : inv.amount_untaxed or 0.0,
                        'tax_amount' :inv.amount_tax or 0.0,
                        'currency_id': inv.currency_id.id,
                        'state' : '1',
                        'nomor_perusahaan':kode_pt,
                        'tahun_penerbit':tahun,
                        'nomor_urut' : nomor_fp,
                        }
                    faktur_obj.create(vals)
        
    @api.multi
    def action_invoice_open(self):
        for inv in self:
            inv.action_create_faktur()
            
        return super(AccountInvoice, self).action_invoice_open()

    # @api.multi
    # def compute_age(self):
    #     self.ensure_one()
    #     diff = 0.0
        
    #     if self.date_due :
    #         due_date = datetime.strptime(self.date_due, '%Y-%m-%d')
    #         print "xxxyyyyy", due_date
    #         now = datetime.now()
    #         diff = now - due_date
    #         print "xxxxxx", diff
    #         self.due_age = diff/365

    @api.multi
    def set_age(self):
        for rec in self:
            if rec.state == 'open': 
                if rec.date_due:
                    dt = rec.date_due
                    print "datedue", dt
                    d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                    d2 = date.today()
                    rd = relativedelta(d2, d1)
                    print "xxxxxxx", float(rd.days)
                    if float(rd.days) < 0.0:
                        rec.due_age = 0.0
                    else:
                        rec.due_age = rd.days
                        print "date_due", rec.due_age
            else :
                rec.due_age = 0.0





