# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime as dt


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Coffee Spesification
    currency2_id = fields.Many2one(
        'res.currency', 'Currency')
    current_sale_price = fields.Float(string="Current Sale Price", compute="_compute_current_price")
    sale_price_ids = fields.One2many(
        'product.sale.price', 'product_tmp_id', string="List Price")
    variety =  fields.Selection([('robusta',"Robusta"),('arabica',"Arabica")],string="Variety")
    grade = fields.Selection([('premium',"Premium"),('standard',"Standard")],string="Grade")
    origin = fields.Many2one('res.country',string='Place of Origin')
    
    @api.depends('sale_price_ids')
    def _compute_current_price(self):
        for item in self:
            latest = False
            latest_price = 0.0
            for price in item.sale_price_ids:
                if not latest:
                    latest = dt.strptime(price.date, '%Y-%m-%d')
                    latest_price = price.rate
                else:
                    if latest < dt.strptime(price.date, '%Y-%m-%d'):
                        latest = dt.strptime(price.date, '%Y-%m-%d')
                        latest_price = price.rate
            item.current_sale_price = latest_price


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Coffee Spesification

    current_sale_price = fields.Float(string="Current Sale Price")
    sale_price_ids = fields.One2many(
        'product.sale.price', 'product_id', string="List Price")


class ProductSalePrice(models.Model):
    _name = 'product.sale.price'
    _description = "Product Daily Sale Price"

    name = fields.Char(string="Name", compute="_get_name")
    date = fields.Date(string="Date", default=lambda self: fields.Date.from_string(fields.Date.context_today(self)))
    product_tmp_id = fields.Many2one('product.template', string="Product")
    product_id = fields.Many2one('product.product', string="Product")
    currency_id = fields.Many2one('res.currency', string="Currency")
    rate = fields.Float(string="Price")


    @api.depends('name','product_tmp_id','currency_id','rate')
    def _get_name(self):
        res = {}
        for x in self :
            name = "%s | %s | %s" % (x.product_tmp_id.name, x.currency_id.name, x.rate)
            print "mmdmdmmdmmdmdm", name
            x.update({'name':name})




