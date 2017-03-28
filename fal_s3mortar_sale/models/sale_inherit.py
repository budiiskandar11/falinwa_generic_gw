# -*- coding: utf-8 -*-

import math

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import amount_to_text_en
from odoo.addons.dos_amount_to_text_id import amount_to_text_id
import odoo.addons.decimal_precision as dp

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        cur = False
        for order in self:
            amount_in_words = False
            amount_untaxed = amount_tax = gross= disc = 0.0
            if order.pricelist_id :
                cur = order.pricelist_id.currency_id.name
            else :
                cur = order.company_id.currency_id.name
            for line in order.order_line:
                gross +=line.product_uom_qty*line.price_unit 
                disc += (line.price_unit*(line.discount/100))*line.product_uom_qty
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                total = amount_untaxed+amount_tax
                amount_in_words = amount_to_text_id.amount_to_text(math.floor(total), lang='id', currency=cur)
            order.update({
                'gross_total':  order.pricelist_id.currency_id.round(gross), 
                'disc_total' : order.pricelist_id.currency_id.round(disc),
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'amount_in_words' : amount_in_words,
            })

            

    gross_total = fields.Monetary(string='Gross Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    disc_total = fields.Monetary(string='Discount Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_in_words = fields.Char(string="Amount in Words",)
    sale_type = fields.Selection([('project','Project'),
        ('retail',"Retail"),
        ('agen',"Agent"),
        ('package','Package')],string="Sale Type")
    package_id  = fields.Many2one('sale.package',string="Package")


    @api.multi
    def load_package(self):
        sale = self.env['sale.order.line']
        if self.filtered(lambda x: x.state == 'draft'):
            if not self.package_id:
                raise UserError(_('No Package to Load.\nPlease select the package for this Order'))
            if self.order_line :
                self.order_line.unlink()
            if self.package_id:
                for x in self.package_id.product_ids:
                    tax_ids = []
                    for tax in x.tax_id :
                        tax_ids.append((4, tax.id, None))

                    vals = {
                            'product_id' : x.product_id.id,
                            'product_uom_qty':x.product_uom_qty,
                            'product_uom': x.product_uom.id,
                            'price_unit': x.price_unit,
                            'order_id':self.id,
                            #'partner_id': self.partner_id.id,
                             'tax_id': tax_ids
                    }
                    sale.create(vals)

        if self.filtered(lambda x: x.state in ('sale', 'done')):
            raise UserError(_('You can not add a sale order line.\nYour Order state is not in Draft'))


