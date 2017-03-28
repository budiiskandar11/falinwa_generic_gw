# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime as dt


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Coffee Spesification
    length = fields.Float(string="Length")
    width   =   fields.Float(string="Width")
    webx    =   fields.Float(string="Webbing")
    weby    =   fields.Float(string="WebY")
    density =   fields.Float(string="Density")
    weigth_gr =  fields.Float(string="Weigth", compute='_compute_weight')

    @api.multi
    def name_get(self):
        return [(template.id, '%s%s%s%s%s%s' % (template.default_code and '[%s] ' % template.default_code or '', template.name, 
                                            template.length and ' P%s,' % int(template.length) or '',
                                            template.width and 'L%s,' % int(template.width) or '',
                                            template.webx and '%sx' % int(template.webx) or '',
                                            template.weby and '%s' % int(template.weby) or '',))
                for template in self]

    @api.multi
    def _compute_weight(self):
        kup = avg = weigth_gr = 0.0
        for x in self :
            kup = x.length*(x.width+4)
            avg = (x.webx+x.weby)/2
            weigth_gr = kup*avg*self.density/571500
            x.update({'weigth_gr':weigth_gr})
        

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _compute_weight(self):
        kup = avg = weigth_gr = 0.0
        for x in self :
            kup = x.length*(x.width+4)
            avg = (x.webx+x.weby)/2
            weigth_gr = kup*avg*self.density/571500
            x.update({'weigth_gr':weigth_gr})
        




