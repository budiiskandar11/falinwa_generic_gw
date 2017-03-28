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

class CashSettlement(models.Model):
    _name ="cash.settlement"
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'utm.mixin']
    _mail_mass_mailing = _('Shipping')
    _description ="Advance Settlements"
    
    
    @api.depends('line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        advance=0.0
        for order in self:
            untaxed_amount = tax = 0.0
            for line in order.line_ids:
                untaxed_amount += line.price_subtotal
                tax += line.price_tax
            advance = self.advance_amount
            order.update({
                'untaxed_amount': order.company_id.currency_id.round(untaxed_amount),
                'taxed_amount': order.company_id.currency_id.round(tax),
                'total_amount': untaxed_amount + tax,
                'diff_amount' : untaxed_amount + tax - advance
            })
    
    @api.model
    def _default_journal(self):
        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type','=', 'purchase'),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    
    
    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string="Partner", domain="[('is_employee','=',True)]")
    responsible_id = fields.Many2one('res.partner', string="Partner", domain="[('is_employee','=',True)]")
    date_submitted = fields.Date(string="Date Submit")
# #     journal_id = fields.Many2one('account.journal', string='Journal', required=False, readonly=True, states={'draft': [('readonly', False)]},default=_default_journal,
#         domain="[('type', '=', ('purchase')")
    currency_id = fields.Many2one('res.currency', string='Currency',
        track_visibility='always',)
    company_id = fields.Many2one('res.company', 'Company', required=False, 
                                 readonly=True,  default=lambda self: self.env['res.company']._company_default_get('cash.settlement'))
    advance_id = fields.Many2one('cash.advance',string='Advance No')
    advance_date = fields.Date(string="Advance Date")
    advance_currency = fields.Many2one('res.currency',string="Currency")
    advance_amount = fields.Float(string="Advance Amount",)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm','Propose'),
            ('waiting', 'Waiting Audit'),
            ('approve', 'Waiting Payment'),
            ('done', 'Settled'),
            ('cancel', 'Cancelled')
            ], 'State', readonly=True, size=32, default='draft',
            help='')
    line_ids = fields.One2many('settlement.lines','settlement_id', string="Lines")
    untaxed_amount = fields.Monetary(string='Untaxed', store=True, readonly=True, track_visibility='always', compute='_amount_all')
    taxed_amount = fields.Monetary(string='Tax', store=True, readonly=True, track_visibility='always', compute='_amount_all')
    total_amount = fields.Monetary(string='Total', store=True, readonly=True, track_visibility='always', compute='_amount_all')
    diff_amount = fields.Monetary(string="Dif Amount",store=True, readonly=True, track_visibility='always', compute='_amount_all')
    voucher_id = fields.Many2one('account.journal', string='Bank/ Cash Payment', required=False, readonly=False,
        domain="[('type', 'in', ('bank','cash'))")
    journal_id = fields.Many2one('account.journal', string='Expense Journal', required=False, readonly=False, 
        domain="[('type', '=', 'purchase')]")
    
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.currency_id = self.company_id.currency_id.id
    
    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        debit = credit = 0.0
#         if self.voucher_type == 'purchase':
#         credit = self._convert_amount(self.amount)
#         elif self.voucher_type == 'sale':
        credit = self._convert_amount(self.total_amount)
        if debit < 0.0: debit = 0.0
        if credit < 0.0: credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        print "Debittt", credit
        move_line = {
                'name': self.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': self.advance_id.account_advance_id.id,
                'move_id': move_id,
                'journal_id': self.journal_id.id,
                'partner_id': self.partner_id.id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency': (sign * abs(self.amount)  # amount < 0 for refunds
                    if company_currency != current_currency else 0.0),
                'date': self.date_submitted,
#                 'date_maturity': self.date_due
            }
        return move_line

    @api.multi
    def account_move_get(self):
        if self.name:
            name = self.name
        elif self.journal_id.sequence_id:
            if not self.journal_id.sequence_id.active:
                raise UserError(_('Please activate the sequence of selected journal !'))
            name = self.journal_id.sequence_id.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move = {
            'name': name,
            'journal_id': self.journal_id.id,
            #'narration': self.narration,
            'date': self.date_submitted,
            'ref': name,
        }
        return move

    @api.multi
    def _convert_amount(self, amount):
        '''
        This function convert the amount given in company currency. It takes either the rate in the voucher (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.
        :param amount: float. The amount to convert
        :param voucher: id of the voucher on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the voucher date
            field in order to select the good rate to use.
        :return: the amount in the currency of the voucher's company
        :rtype: float
        '''
        for voucher in self:
            return voucher.currency_id.compute(amount, voucher.company_id.currency_id)

    @api.multi
    def voucher_move_line_create(self, line_total, move_id, company_currency, current_currency):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        for line in self.line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.price_subtotal:
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context,
            # so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(line.price_unit*line.quantity)
            
            print "amouuuuunntttt1", amount
            move_line = {
                'journal_id': self.journal_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': self.partner_id.id,
#                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
#                 'credit': abs(amount) if self.voucher_type == 'sale' else 0.0,
                'credit': 0.0,
                'debit': abs(amount),
                'date': self.date_submitted,
                'tax_ids': [(4,t.id) for t in line.settlement_line_tax_ids],
                'amount_currency': line.price_subtotal if current_currency != company_currency else 0.0,
            }

            self.env['account.move.line'].with_context(apply_taxes=True).create(move_line)
        return line_total

    @api.multi
    def action_move_line_create(self):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        for voucher in self:
            local_context = dict(self._context, force_company=voucher.journal_id.company_id.id)
#             if voucher.move_id:
#                 continue
            company_currency = voucher.journal_id.company_id.currency_id.id
            current_currency = voucher.currency_id.id or company_currency
            # we select the context to use accordingly if it's a multicurrency case or not
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = local_context.copy()
            ctx['date'] = voucher.date_submitted
            ctx['check_move_validity'] = False
            # Create the account move record.
            move = self.env['account.move'].create(voucher.account_move_get())
            # Get the name of the account_move just created
            # Create the first line of the voucher
            move_line = self.env['account.move.line'].with_context(ctx).create(voucher.first_move_line_get(move.id, company_currency, current_currency))
            lines_total = move_line.debit - move_line.credit
#             if voucher.voucher_type == 'sale':
#                 line_total = line_total - voucher._convert_amount(voucher.tax_amount)
#             elif voucher.voucher_type == 'purchase':
            line_total = lines_total + voucher._convert_amount(voucher.taxed_amount)
            # Create one move line per voucher line where amount is not 0.0
            line_total = voucher.with_context(ctx).voucher_move_line_create(line_total, move.id, company_currency, current_currency)

            # Add tax correction to move line if any tax correction specified
#             if voucher.tax_correction != 0.0:
#                 tax_move_line = self.env['account.move.line'].search([('move_id', '=', move.id), ('tax_line_id', '!=', False)], limit=1)
#                 if len(tax_move_line):
#                     tax_move_line.write({'debit': tax_move_line.debit + voucher.tax_correction if tax_move_line.debit > 0 else 0,
#                         'credit': tax_move_line.credit + voucher.tax_correction if tax_move_line.credit > 0 else 0})

            # We post the voucher.
            voucher.write({
                'move_id': move.id,
#                 'state': 'posted',
                
            })
            move.post()
        return True
    
#     @api.multi
#     def _convert_amount(self, amount):
#        
#         for voucher in self:
#             return voucher.currency_id.compute(amount, voucher.company_id.currency_id)
#     
class SettlementLines(models.Model):
    _name = "settlement.lines"
    _description = "Settlement Lines"
    
    @api.depends('quantity', 'price_unit', 'settlement_line_tax_ids')
    def _compute_price(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.settlement_line_tax_ids.compute_all(price, line.settlement_id.currency_id, line.quantity, product=None, partner=line.settlement_id.partner_id)
            
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
    
    def _get_default_uom_id(self):
        return self.env["product.uom"].search([], limit=1, order='id').id       
    
    name = fields.Text(string='Description', required=True)
    date = fields.Date(string="Date")
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',default=_get_default_uom_id,
        ondelete='set null', index=True, oldname='uos_id')
    settlement_id = fields.Many2one('cash.settlement',string="Settlement")
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)
    account_id = fields.Many2one('account.account', string='Account',
        required=True, domain=[('deprecated', '=', False)],
        
        help="The income or expense account related to the selected product.")
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    price_tax = fields.Monetary(string='Tax',
        store=True, readonly=True, compute='_compute_price')
    price_total = fields.Monetary(string='Total',
        store=True, readonly=True, compute='_compute_price')
    price_subtotal = fields.Monetary(string='Subtotal',
        store=True, readonly=True, compute='_compute_price')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
        required=True, default=1)
    company_id = fields.Many2one('res.company', string='Company',
        related='settlement_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='settlement_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='settlement_id.currency_id', store=True)
    #company_currency_id = fields.Many2one('res.currency', related='settlement_id.company_currency_id', readonly=True)
    settlement_line_tax_ids = fields.Many2many('account.tax',
        'settlement_line_tax', 'settlement_line_id', 'tax_id',
        string='Taxes', domain=[('type_tax_use','!=','none'), '|', ('active', '=', False), ('active', '=', True)], oldname='invoice_line_tax_id')
    expense_type = fields.Many2one('expense.type', string="Expense Group", required=True)
    
    
    @api.onchange('expense_type')
    def _onchange_expense_type(self):
        if self.expense_type:
            self.account_id = self.expense_type.account_id.id


    
    