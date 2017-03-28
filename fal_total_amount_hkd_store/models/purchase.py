# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp



class purchase_order(models.Model):
    _name = "purchase.order"
    _inherit = "purchase.order"

    @api.multi
    def _amount_untaxed_hkd(self):
        cur_obj = self.env['res.currency']
        untaxed_amount_hkd = 0.0
        hkd_currency = cur_obj.search([('name', '=', 'HKD')], limit=1)[0]
        print "xxxxxxx", hkd_currency
        for order in self:
            if order.currency_id != hkd_currency:
                cur = hkd_currency.with_context(date=self.date_order or fields.Date.context_today(self))[0]
                print "xxxxxxx", cur
                order['untaxed_amount_hkd'] = cur.compute(order['untaxed_amount'], order.currency_id)
                print "cccccccc", order['untaxed_amount_hkd']

   

    untaxed_amount_hkd = fields.Monetary(
        compute='_amount_untaxed_hkd',
        string='Untaxed Amount (HKD)',
        help="The untaxed amount in HKD."
    )
    amount_total_hkd = fields.Char(
        string='Total (HKD)',
        help="The total amount in HKD."
    )
    total_uninvoice = fields.Char(string='Total Uninvoice', help="The total uninvoice.")
    total_uninvoice_hkd = fields.Char(
        string='Total Uninvoice (HKD)',
        help="The total uninvoice in HKD."
    )



# end of purchase_order()
