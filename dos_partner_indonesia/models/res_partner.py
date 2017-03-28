# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.modules import get_module_resource
from odoo.osv.expression import get_unaccent_wrapper
from odoo.exceptions import UserError, ValidationError
from odoo.osv.orm import browse_record


class ResPartner(models.Model):
    
    _inherit = "res.partner"

    @api.model
    def create(self,vals):

        if not vals.get('ref', False):
            if vals.get('is_company', False):
                if vals.get('customer', False):
                    vals['ref'] = self.env['ir.sequence'].next_by_code('customer.code') or 'New'
                elif vals.get('supplier', False):
                    vals['ref'] = self.env['ir.sequence'].next_by_code('supplier.code') or 'New'
                else:
                    vals['ref'] = self.env['ir.sequence'].next_by_code('sc.code') or 'New'
        return super(ResPartner, self).create(vals)
    
    npwp= fields.Char('NPWP')
    is_employee = fields.Boolean(string="Employee")
    is_holding = fields.Boolean(string="Holding")
    supplier_ref    =  fields.Many2one('res.partner', string="Supplier Ref")
    birthday = fields.Date(string="Ulang tahun")
    group_id = fields.Many2one('res.partner',string="Group Company")

    _sql_constraints = [
        ('npwp_uniq', 'unique(npwp)', 'The npwp of the customer must be unique!'),
    ]
# end of res_partner()
