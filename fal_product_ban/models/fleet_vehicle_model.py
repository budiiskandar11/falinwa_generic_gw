# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime as dt


class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    tire_available_ids = fields.Many2many('product.template', 'product_model_tag_rel', 'fleet_product_rel', 'product_id', string="Available Tire")

