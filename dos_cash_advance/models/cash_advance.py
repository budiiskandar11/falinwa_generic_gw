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

class CashAdvance(models.Model):
    _name = "cash.advance"
    _description = "Cash Advance"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "date desc, id desc"
    
    
    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in',('bank','cash')),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    
    
    @api.one
    @api.depends('line_ids.amount', 'currency_id', 'company_id')
    def _compute_amount(self):
        self.amount_total = sum((line.amount) for line in self.line_ids)
        
    
    
    
    description = fields.Char(string='Description', size=256, required=True ,readonly=True, states={'draft': [('readonly', False)]})
    name = fields.Char(string='Name')
    responsible = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string="Partner", domain="[('is_employee','=',True)]")
    date = fields.Date(string='Date', readonly=True, select=True, states={'draft': [('readonly', False)]}, help="Effective date for accounting entries", default=lambda self: fields.Date.from_string(fields.Date.context_today(self)))
    journal_id = fields.Many2one('account.journal', string='Bank/ Cash Payment', required=False, readonly=True, states={'draft': [('readonly', False)]},default=_default_journal,
        domain="[('type', 'in', ('bank','cash'))")
    account_id = fields.Many2one('account.account', string='Account', required=False, readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('cash.advance.line', 'advance_id', string='Voucher Lines', readonly=True, states={'draft': [('readonly', False)]})
    narration = fields.Text('Notes', readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=False, readonly=True, states={'draft': [('readonly', False)]},
        track_visibility='always')
    company_id = fields.Many2one('res.company', 'Company', required=False, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('cash.advance'))
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm','Propose'),
            ('proforma', 'Waiting Approval'),
            ('approve', 'Waiting Payment'),
            ('posted', 'Paid'),
            ('cancel', 'Cancelled')
            ], 'State', readonly=True, size=32, default='draft',
            help='')
    
    account_advance_id = fields.Many2one('account.account', string='Advance Account', required=False)    
#         'create_uid'    : fields.many2one('res.users','Create By'),
#         'date_create'   : fields.datetime('Date Create'),
#         'advance_type'  : fields.many2one('cash.advance.type', 'Type Advance'),
#         'department_id' : fields.many2one('hr.department','Department'),
    amount_total = fields.Monetary(string='Total',
        store=True, readonly=True, compute='_compute_amount',currency_field='currency_id')
    
    
    
    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id


    @api.multi
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        for line in self:
            prec = self.env['decimal.precision'].precision_get('Account')
            name = self.name + '' + self.description
            company_currency = line.company_id.currency_id
            current_currency = line.currency_id
            amount = current_currency.compute(line.amount_total, company_currency)
            sign = (line.journal_id.type == 'bank' or line.journal_id.type == 'cash' and 1) or -1
            move_line_1 = {
                'name': name,
                'account_id': line.account_advance_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': line.journal_id.id,
                'partner_id': line.partner_id.id,
#                 'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
            }
            move_line_2 = {
                'name': name,
                'account_id': line.journal_id.default_credit_account_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'journal_id': line.journal_id.id,
                'partner_id': line.partner_id.id,
#                 'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
            }
            move_vals = {
                'ref': line.name,
                'date': line.date or False,
                'journal_id': line.journal_id.id,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            }
            move = self.env['account.move'].create(move_vals)
           
#             created_moves |= move

        return [x.id for x in created_moves]
    
    @api.multi
    def create_settlement(self):
        settle_obj = self.env['cash.settlement']
        for o in self:
            val_line = {
                'name' : o.line_ids.name,
                'price_unit' : 0.0,
                'account_id' : o.account_advance_id.id,
                'expense_type' : o.line_ids.expense_type.id,
                }
            val = {
                'advance_id' :o.id,
                'advance_date' : o.date,
                'advance_amount': o.amount_total,
                'partner_id':o.partner_id.id,
                'currency_id': o.currency_id.id,
                'line_ids': [(0, 0, val_line)],
                'name': 'NAME'
                }
            settle = settle_obj.create(val)
            
        return
    
    @api.multi
    def propose(self):
        return self.write({'state': 'confirm'})

    @api.multi
    def approve2(self):
        return self.write({'state': 'approve'})

    @api.multi
    def approve(self):
        return self.write({'state': 'proforma'})
    
    @api.multi
    def validate(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        advance_obj = self.filtered(lambda inv: inv.state == 'draft')
        advance_obj.create_move()
        advance_obj.create_settlement()
        
        return self.write({'state': 'posted'})
          

class CashAdvanceLines(models.Model):
    _name   ="cash.advance.line"
    _description ="Cash Advance Lines"
    _order = 'move_line_id'
    
    
    advance_id = fields.Many2one('cash.advance', string='Advance', required=1, ondelete='cascade')
    name = fields.Char(string='Description', size=256)
    partner_id = fields.Many2one('res.partner', related='advance_id', string='Partner')
    amount = fields.Float(string='Amount')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    move_line_id = fields.Many2one('account.move.line', string='Journal Item')
#     date_original = fields.Date(related='account.move.line', string='Date', readonly=1)
    expense_type = fields.Many2one('expense.type', string="Expense Group", required=True)
     



