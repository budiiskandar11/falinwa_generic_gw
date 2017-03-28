from odoo import fields, models, api, _
import openerp.addons.decimal_precision as dp


class account_invoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"

    def _amount_line_tax(self, line):
        val = 0.0
        rate_ids = self.env['res.currency'].search([('name', '=', 'HKD')], limit=1)
        taxes_ids = [x.id for x in line.invoice_line_tax_ids]
        for c in self.env['account.tax'].compute_all(taxes_ids, line.price_unit * (1-(line.discount or 0.0)/100.0), rate_ids[0], line.quantity, line.product_id.id, line.invoice_id.partner_id.id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    @api.multi
    def _get_invoice_line_fal(self):
        result = {}
        for line in self.env['account.invoice.line'].browse():
            result[line.invoice_id.id] = True
        return result.keys()

    @api.multi
    def _get_invoice_tax_fal(self):
        result = {}
        for tax in self.env['account.invoice.tax'].browse():
            result[tax.invoice_id.id] = True
        return result.keys()

    @api.multi
    def _amount_all_hkd(self):
        cur_obj = self.env['res.currency']
        res = {}
        context = dict(self._context)
        ctx = context.copy()
        for invoice in self:
            ctx.update({'date': invoice.date_invoice})
            rate_ids = cur_obj.search([('name', '=', 'HKD')], limit=1)
            cur = invoice.currency_id
            temp = amount_tax = amount_untaxed = 0.0
            for line in invoice.invoice_line_ids:
                amount_untaxed += line.price_subtotal
            for line in invoice.tax_line_ids:
                amount_tax += line.amount
            temp = amount_untaxed + amount_tax
            for rate_id in cur_obj.browse(rate_ids):
                if cur != rate_id:
                    temp = cur_obj.compute(cur.id, rate_id.id, temp, context=ctx)
            res[invoice.id] = cur_obj.round(temp)
        return res

    @api.multi
    def _amount_untaxed_hkd(self):
        cur_obj = self.env['res.currency']
        res = {}
        context = dict(self._context)
        ctx = context.copy()
        for invoice in self:
            ctx.update({'date': invoice.date_invoice})
            rate_ids = cur_obj.search([('name', '=', 'HKD')], limit=1)
            cur = invoice.currency_id
            amount_untaxed = 0.0
            for line in invoice.invoice_line_ids:
                amount_untaxed += line.price_subtotal
            amount_untaxed = cur_obj.round(amount_untaxed)
            for rate_id in cur_obj.browse(rate_ids):
                if cur != rate_id:
                    amount_untaxed = cur_obj.compute(cur.id, rate_id.id, amount_untaxed, context=ctx)
            res[invoice.id] = cur_obj.round(amount_untaxed)
        return res

    @api.multi
    def _amount_ballance_hkd(self):
        """Function of the field residua. It computes the residual amount (balance) for each invoice"""
        context = dict(self._context)
        ctx = context.copy()
        result = {}
        currency_obj = self.env['res.currency']
        rate_ids = currency_obj.search([('name', '=', 'HKD')], limit=1)
        for invoice in self:
            temp = invoice.residual
            cur = invoice.currency_id
            for rate_id in currency_obj.browse(rate_ids):
                if cur != rate_id:
                    temp = currency_obj.compute(cur.id, rate_id.id, temp, context=ctx)
            result[invoice.id] = currency_obj.round(temp)
        return result

    untaxed_amount_hkd = fields.Float(
        compute='_amount_untaxed_hkd',
        string='Subtotal (HKD)',
        track_visibility='always',
    )
    amount_total_hkd = fields.Float(
        compute='_amount_all_hkd',
        string='Total (HKD)',
        help="The total amount in HKD."
    )
    amount_ballance_hkd = fields.Float(
        compute='_amount_ballance_hkd',
        string='Balance (HKD)',
        help="The balance amount in HKD."
    )

# end of account_invoice()


class account_move_line(models.Model):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    @api.multi
    def _amount_all_to_hk(self, field_name, arg):
        currency_pool = self.env['res.currency']
        rs_data = {}
        for line in self:
            context = dict(self._context)
            ctx = context.copy()
            ctx.update({'date': line.date})
            res = {}
            res['fal_debit_hk'] = 0.0
            res['fal_credit_hk'] = 0.0
            rate_ids = currency_pool.search([('name', '=', 'HKD')], context=ctx, limit=1)
            for rate_id in currency_pool.browse(rate_ids, ctx):
                rate_hk = rate_id
                origin_currency = line.journal_id.company_id.currency_id
                if origin_currency == rate_id:
                    res['fal_debit_hk'] = abs(line.debit)
                    res['fal_credit_hk'] = abs(line.credit)
                else:
                    # always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                    res['fal_debit_hk'] = currency_pool.compute(origin_currency.id, rate_hk.id, abs(line.debit), context=ctx)
                    res['fal_credit_hk'] = currency_pool.compute(origin_currency.id, rate_hk.id, abs(line.credit), context=ctx)

                rs_data[line.id] = res
        return rs_data

    fal_debit_hk = fields.Float(
        compute='_amount_all_to_hk',
        string='Debit (HKD)',
        help="Debit in HKD."
    )
    fal_credit_hk = fields.Float(
        compute='_amount_all_to_hk',
        string='Credit (HKD)',
        help="Credit in HKD."
    )

# end of account_move_line()
