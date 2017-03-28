# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp


class sale_order(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    def _amount_line_tax(self, line):
        val = 0.0
        rate_ids = self.env['res.currency'].search([('name', '=', 'HKD')], limit=1)
        taxes_ids = [x.id for x in line.tax_id]
        for c in self.env['account.tax'].compute_all(taxes_ids, line.price_unit, line.product_uom_qty, line.product_id.id, line.order_id.partner_id.id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    @api.multi
    def _get_order_fal(self):
        result = {}
        for line in self.env['sale.order.line'].browse():
            result[line.order_id.id] = True
        return result.keys()

    @api.multi
    def _get_invoice_ids_fal(self):
        invoices = {}
        for invoice_ids in self.env['account.invoice'].browse():
            invoices[invoice_ids.id] = True
        sale_ids = []
        if invoices:
            sale_ids = self.env['sale.order'].search([('invoice_ids', 'in', invoices.keys())])
        return sale_ids

    @api.multi
    def _amount_untaxed_hkd(self):
        cur_obj = self.env['res.currency']
        res = {}
        context = dict(self._context)
        ctx = context.copy()
        for order in self:
            ctx.update({'date': order.date_order})
            rate_ids = cur_obj.search([('name', '=', 'HKD')], limit=1)
            val1 = 0.0
            cur = order.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
            val1 = cur_obj.round(val1)
            for rate_id in cur_obj.browse(rate_ids):
                if cur != rate_id:
                    val1 = cur_obj.compute(cur.id, rate_id.id, val1, context=ctx)
            res[order.id] = cur_obj.round(val1)
        return res

    @api.multi
    def _amount_all_hkd(self):
        cur_obj = self.env['res.currency']
        res = {}
        context = dict(self._context)
        ctx = context.copy()
        for order in self:
            ctx.update({'date': order.date_order})
            rate_ids = cur_obj.search([('name', '=', 'HKD')], limit=1)
            temp = val = val1 = 0.0
            cur = order.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(line)
            temp = (cur_obj.round(cur, val) + cur_obj.round(cur, val1))
            for rate_id in cur_obj.browse(cr, uid, rate_ids, ctx):
                if cur != rate_id:
                    temp = cur_obj.compute(cur.id, rate_id.id, temp, context=ctx)
            res[order.id] = cur_obj.round(cur, temp)
        return res

    @api.multi
    def _total_uninvoice(self, field_name, arg):
        res = {}
        cur_obj = self.env['res.currency']
        invoice_obj = self.env['account.invoice']
        context = dict(self._context)
        ctx = context.copy()
        for order in self:
            ctx.update({'date': order.date_order})
            total_invoice_ammount = total_order_tax = total_invoice_tax = total_order_subtotal = total_invoice_subtotal = 0.0
            origin_currency = order.currency_id
            temp = []
            for invoice_id in order.invoice_ids:
                if invoice_id.state not in ('draft', 'cancel'):
                    temp.append(invoice_id.id)
                    # Odoo v9 doesn't support order_policy
                    # if order.order_policy == 'manual':
                    #     total_invoice_ammount += invoice_id.amount_total
                    # else:
                    #     temp.append(invoice_id.id)
            for order_line in order.order_line:
                total_order_subtotal += order_line.price_subtotal
                total_order_tax += self._amount_line_tax(order_line)
                # Odoo v9 doesn't support order_policy, should bring the sales flow to fallback value (without 'manual' order_policy).
                # if order.order_policy != 'manual':
                for invoice_line in order_line.invoice_lines:
                    if invoice_line.invoice_id.id in temp:
                        total_invoice_subtotal += invoice_line.price_subtotal
                        total_invoice_tax += invoice_obj._amount_line_tax(invoice_line)
                total_invoice_ammount = total_invoice_subtotal + total_invoice_tax
            res[order.id] = cur_obj.round(origin_currency, (total_order_subtotal + total_order_tax) - total_invoice_ammount)
        return res

    @api.multi
    def _total_uninvoice_hkd(self, field_name, arg):
        cur_obj = self.env['res.currency']
        invoice_obj = self.env('account.invoice')
        res = {}
        context = dict(self._context)
        ctx = context.copy()
        for order in self:
            ctx.update({'date': order.date_order})
            rate_ids = cur_obj.search([('name', '=', 'HKD')], context=ctx, limit=1)
            total_invoice_ammount = total_order_tax = total_invoice_tax = result = total_order_subtotal = total_invoice_subtotal = 0.0
            origin_currency = order.currency_id
            temp = []
            for invoice_id in order.invoice_ids:
                if invoice_id.state not in ('draft', 'cancel'):
                    temp.append(invoice_id.id)
                    # Odoo v9 doesn't support order_policy, should bring the sales flow to fallback value (without 'manual' order_policy).
                    # if order.order_policy == 'manual':
                    #     total_invoice_ammount += invoice_id.amount_total
                    # else:
                    #     temp.append(invoice_id.id)
            for order_line in order.order_line:
                total_order_subtotal += order_line.price_subtotal
                total_order_tax += self._amount_line_tax(order_line)
                # Odoo v9 doesn't support order_policy, should bring the sales flow to fallback value (without 'manual' order_policy).
                # if order.order_policy != 'manual':
                for invoice_line in order_line.invoice_lines:
                    if invoice_line.invoice_id.id in temp:
                        total_invoice_subtotal += invoice_line.price_subtotal
                        total_invoice_tax += invoice_obj._amount_line_tax(invoice_line)
                total_invoice_ammount = total_invoice_subtotal + total_invoice_tax
            result = (total_order_subtotal + total_order_tax) - total_invoice_ammount
            for rate_id in cur_obj.browse(rate_ids, ctx):
                if origin_currency != rate_id:
                    result = cur_obj.compute(origin_currency.id, rate_id.id, result, context=ctx)
            res[order.id] = cur_obj.round(origin_currency, result)
        return res

    untaxed_amount_hkd = fields.Float(
        compute='_amount_untaxed_hkd',
        string='Untaxed Amount (HKD)',
        help="The untaxed amount in HKD."
    )
    amount_total_hkd = fields.Float(
        compute='_amount_all_hkd',
        string='Total (HKD)',
        help="The total amount in HKD."
    )
    total_uninvoice = fields.Float(
        compute='_total_uninvoice',
        string='Total Uninvoice',
        help="The total uninvoice."
    )
    total_uninvoice_hkd = fields.Float(
        compute='_total_uninvoice_hkd',
        string='Total Uninvoice (HKD)',
        help="The total uninvoice in HKD."
    )


# end of sale_order()
