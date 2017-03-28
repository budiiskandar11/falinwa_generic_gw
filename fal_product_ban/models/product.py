# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime as dt


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fleet_available_ids = fields.Many2many('fleet.vehicle.model', 'fleet_model_tag_rel', 'product_fleet_rel', 'product_id', string="Available Car")

