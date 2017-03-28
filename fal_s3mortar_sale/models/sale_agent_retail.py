import math

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import amount_to_text_en
from odoo.addons.dos_amount_to_text_id import amount_to_text_id
import odoo.addons.decimal_precision as dp


class SaleAgent(models.Model):
    _name = "sale.agent"
    _description = "Sale Package for S3Mortar"

    name = fields.Char(string="Package Name")
    partner_id  = fields.Many2one('res.partner',string="Customer")
    team_id     = fields.Many2one('crm.team', string="Type")
    currency_id = fields.Many2one('res.currency', string="Currency")
    dp_account = fields.Many2one('account.account', string="Account")
    dp_amount = fields.Float(string="Package Price")
    product_ids = fields.One2many('package.lines','package_id',string="Product Lines")
    invoice_id  =   fields.Many2one('account.invoice', string="Invoice Number")
    invoice_paid_date = fields.Datetime(string="Invoice Paid Date")

    @api.multi
    def create_invoice(self):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        if self.dp_amount <= 0.00:
            raise UserError(_('Sales Deposit cannot be made with amount less then 0'))
        for order in self :
            invoice = inv_obj.create({
                'name': order.name,
                'origin': order.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': order.partner_id.property_account_receivable_id.id,
                'partner_id': order.partner_id.id,
                #'partner_shipping_id': order.partner_shipping_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': order.name,
                    'origin': order.name,
                    'account_id': order.dp_account.id,
                    'price_unit': order.dp_amount,
                    'quantity': 1.0,
                    'discount': 0.0,
                    # 'uom_id': self.product_id.uom_id.id,
                    #'product_id': self.product_id.id,
                    #'sale_line_ids': [(6, 0, [so_line.id])],
                    #'invoice_line_tax_ids': [(6, 0, tax_ids)],
                    #'account_analytic_id': order.project_id.id or False,
                })],
                #'currency_id': order.pricelist_id.currency_id.id,
                #'payment_term_id': order.payment_term_id.id,
                #'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
                'team_id': order.team_id.id,
                #'comment': order.note,
            })
            # invoice.compute_taxes()
            # invoice.message_post_with_view('mail.message_origin_link',
            #             values={'self': invoice, 'origin': order},
            #             subtype_id=self.env.ref('mail.mt_note').id)
        self.write({'invoice_id':invoice.id})
        return True