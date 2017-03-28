# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    asset_id = fields.Many2one('account.asset.asset', string='Asset No.', track_visibility='onchange')
    manual_book = fields.Binary(string="Manual Book")
    # state = fields.Selection([
    #         ('draft','Draft'),
    #         ('ready', 'Idle'),
    #         ('on_production', 'On Production'),
    #         ('maintenance', 'Maintenance'),
    #     ], string='Status', index=True, readonly=True, default='draft',
    #     track_visibility='onchange', copy=False,)