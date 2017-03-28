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


class SaleOrder(models.Model):
    _inherit = "sale.order.line"

    price_kg    = fields.Float(string="Price /Kg")
    price_cal   = fields.Float(string="Price /Pcs", compute="_compute_price")

    @api.depends('price_kg')
    def _compute_price(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_kg * line.product_id.weigth_gr / 1000.0
            line.update({
                'price_cal': price,
                
            })