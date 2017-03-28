# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta, MO
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import odoo.addons.decimal_precision as dp

class TruckIn(models.Model):
    _name = 'asalan'
    _decription = "Truck In Models"

    name        = fields.Char(string="Name", compute="_get_name")
    date        = fields.Date(string="Date", default=lambda self: fields.Date.from_string(fields.Date.context_today(self)))
    user_id     = fields.Many2one('res.users', string="Responsible", readonly=True, default=lambda self: self.env.user)
    partner_id  =   fields.Many2one('res.partner', string="Supplier", domain="[('supplier','=',True)]")
    allocated_partner_id = fields.Many2one('res.partner', string="Allocated Partner", domain="[('supplier_ref','=',partner_id)]")
    truck_no        = fields.Char(string='Truck No', size=4)
    truck_prefix    = fields.Char(string="Prefix", size=2)
    truck_suffix   = fields.Char(string="suffix", size=2)
    product_id      = fields.Many2one('product.template',string="Product")
    has_purchase    = fields.Boolean(string="Has Purchase")
    purchase_id     = fields.Many2one('purchase.order', string="Contract No")
    estimated_qty   = fields.Float(string='Qty Estimated')
    price_id        = fields.Many2one('product.sale.price')
    state           = fields.Selection([('draft','Draft'),('truck_in','Truck In'),
        ('weight_in','Weight In'),('weight_out','Weight Out'),('qc','On Inspection'),('truck_out','Truck Out'),
        ('price','Price Adjustment'),('paid','Done')],string="State")

    @api.depends('partner_id','allocated_partner_id','truck_no','purchase_id')
    def _get_name(self):
        res = {}
        
        for x in self :
            date = fields.Date.from_string(x.date)
            year = date.strftime('%y')

            if x.purchase_id :
                kontrak = x.purchase_id.name
            else:
                kontrak = '0000'

            print "xxxxx", date, year
            name = "%s%s%s%s-%s" % (x.partner_id.ref, x.allocated_partner_id.ref,x.truck_no,year,kontrak)
            print "mmdmdmmdmmdmdm", name
            x.update({'name':name})