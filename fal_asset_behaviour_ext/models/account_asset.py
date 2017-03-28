# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil import rrule


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    def _check_recursion(self, cr, uid, ids, context=None):
        for id in ids:
            visited_branch = set()
            visited_node = set()
            res = self._check_cycle(
                cr, uid, id, visited_branch, visited_node, context=context)
            if not res:
                return False

        return True

    def _check_cycle(
            self, cr, uid, id, visited_branch, visited_node, context=None):
        if id in visited_branch:  # Cycle
            return False

        # Already tested don't work one more time for nothing
        if id in visited_node:
            return True

        visited_branch.add(id)
        visited_node.add(id)

        # visit child using DFS
        asset_category = self.browse(cr, uid, id, context=context)
        for child in asset_category.child_ids:
            res = self._check_cycle(
                cr, uid, child.id, visited_branch,
                visited_node, context=context)
            if not res:
                return False
        visited_branch.remove(id)
        return True

    fal_type = fields.Selection(
        [('view', 'Account View'), ('normal', 'Normal')], 'Type',
        required=True, default='normal')
    parent_id = fields.Many2one(
        'account.asset.category', 'Parent Account',
        domain="[('fal_type', '=', 'view')]")
    child_ids = fields.One2many(
        'account.asset.category', 'parent_id', 'Children', copy=False)
    fal_asset_account_id = fields.Many2one(
        'account.account', string='Asset Account')

    _constraints = [(
        _check_recursion,
        _('Error! You cannot create recursive hierarchy'), ['parent_id'])]


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    fal_purchase_date = fields.Date(
        'Purchase Date', readonly=True,
        states={'draft': [('readonly', False)]})
    fal_original_purchase_value = fields.Float(
        'Original Purchase Value', readonly=True,
        digits=0, states={'draft': [('readonly', False)]})
    fal_second_depreciation_date = fields.Date(
        'Second Depreciation Date', readonly=True,
        states={'draft': [('readonly', False)]})
    method_time = fields.Selection(
        selection_add=[('percentage purchase value',
                        'By percentage of the original purchase value')])
    fal_annual_percentage = fields.Float('Annual Percentage')
    fal_annual_depreciation = fields.Float(
        compute='_compute_fal_annual_depreciation',
        string='Annual Depreciation')
    fal_asset_number = fields.Char('Asset Number', size=64)

    @api.model
    def create(self, vals):
        seq_obj = self.env['ir.sequence']
        model = 'fal.account.asset.asset'
        vals['fal_asset_number'] = seq_obj.next_by_code(model) or 'New'
        return super(AccountAssetAsset, self).create(vals)

    # complety overide Odoo real method
    def _compute_board_amount(
            self, sequence, residual_amount, amount_to_depr,
            undone_dotation_number, posted_depreciation_line_ids,
            total_days, depreciation_date):
        res = super(AccountAssetAsset, self)._compute_board_amount(
            sequence, residual_amount, amount_to_depr, undone_dotation_number,
            posted_depreciation_line_ids, total_days, depreciation_date)
        anm = self.fal_annual_depreciation / 12 * self.method_period
        if sequence != undone_dotation_number:
            if self.method == 'linear':
                if self.prorata and self.category_id.type == 'purchase':
                    dep_date = self.fal_second_depreciation_date
                    # dep_date2 = depreciation_date.strftime('%j')
                    fal_dep_time = datetime.strptime(dep_date, DF)
                    fal_first_dep_time = datetime.strptime(self.date, DF)
                    # fal_dep_date = fal_dep_time.date().strftime('%j')
                    gap_first_second = \
                        (fal_dep_time.date() - fal_first_dep_time.date()).days

                    gpm = float(
                        gap_first_second / float(self.method_period * 30))

                    if sequence == 1:
                        res = (amount_to_depr / self.method_number) * gpm
                        if self.method_time == 'percentage purchase value':
                            res = anm * gpm
                    else:
                        if self.method_time == 'percentage purchase value':
                            res = anm
                else:
                    if self.method_time == 'percentage purchase value':
                            res = anm
        return res

    @api.one
    @api.depends('fal_annual_percentage', 'method_time',
                 'fal_original_purchase_value')
    def _compute_fal_annual_depreciation(self):
        if self.method_time == 'percentage purchase value':
            purchase_value = self.fal_original_purchase_value
            percentage = self.fal_annual_percentage
            self.fal_annual_depreciation = purchase_value * percentage / 100
        else:
            self.fal_annual_depreciation = 0.00

    @api.one
    @api.depends('value', 'salvage_value', 'depreciation_line_ids')
    def _amount_residual(self):
        total_amount = 0.0
        for line in self.depreciation_line_ids:
            if line.move_check:
                total_amount += line.amount
        self.value_residual = self.value - total_amount - self.salvage_value

    # completely override odoo method
    @api.onchange('method_time')
    def onchange_method_time(self):
        if self.method_time not in ['number', 'percentage purchase value']:
            self.prorata = False

    # completely override odoo method
    @api.one
    @api.constrains('prorata', 'method_time')
    def _check_prorata(self):
        method = ['number', 'percentage purchase value']
        err_msg = 'Prorata temporis can be applied only for time method ' \
                  '"number of depreciations and percentage purchase value".'
        if self.prorata and self.method_time not in method:
            raise ValidationError(_(err_msg))

    @api.multi
    def compute_depreciation_board(self):
        self.ensure_one()
        dep_line_ids = self.depreciation_line_ids
        posted_line_ids = dep_line_ids.filtered(lambda x: x.move_check)
        unposted_line_ids = dep_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines.
        # We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual
            asset_value = self.value
            if self.prorata:
                last_dep_date = self._get_last_depreciation_date()[self.id]
                dep_date = datetime.strptime(last_dep_date, DF).date()
            else:
                # depreciation_date = 1st of January of purchase year
                asset_date = datetime.strptime(self.date, DF).date()
                # if we already have some previous validated entries,
                # starting date isn't 1st January but last entry+method period
                if posted_line_ids and posted_line_ids[0].depreciation_date:
                    posted_dep_date = posted_line_ids[0].depreciation_date
                    last_dep_date = \
                        datetime.strptime(posted_dep_date, DF).date()
                    months = +self.method_period
                    dep_date = last_dep_date + relativedelta(months=months)
                else:
                    dep_date = asset_date
            day = dep_date.day
            month = dep_date.month
            year = dep_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(
                dep_date, total_days)
            for x in range(len(posted_line_ids), undone_dotation_number):
                sequence = x + 1
                amount = self._compute_board_amount(
                    sequence, residual_amount, amount_to_depr,
                    undone_dotation_number, posted_line_ids, total_days,
                    dep_date)
                amount = self.currency_id.round(amount)
                residual_amount -= amount
                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': (self.code or '') + '/' + str(sequence),
                    'remaining_value': residual_amount,
                    'depreciated_value':
                        asset_value - (self.salvage_value + residual_amount),
                    'depreciation_date': dep_date.strftime(DF),
                }
                commands.append((0, False, vals))
                # Considering Depr. Period as months
                if sequence == 1 and self.prorata:
                    scnd_dep_date = self.fal_second_depreciation_date
                    dep_date = datetime.strptime(scnd_dep_date, DF).date()
                else:
                    dep_date = date(year, month, day) + relativedelta(
                        months=+self.method_period)

                day = dep_date.day
                month = dep_date.month
                year = dep_date.year
        self.write({'depreciation_line_ids': commands})
        return True

    def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
        res = super(AccountAssetAsset, self)._compute_board_undone_dotation_nb(
            depreciation_date, total_days)
        period = self.method_period
        value_residual = self.value_residual
        fal_dep = self.fal_annual_depreciation
        if self.method_time == 'percentage purchase value':
            y = (fal_dep / 12 * period)
            undone_dotation_number = int(value_residual / y) + 1

            if self.prorata and self.category_id.type == 'purchase':
                fdep = self.fal_second_depreciation_date
                dep_date1 = datetime.strptime(fdep, DF).date()
                dep_date2 = datetime.strptime(self.date, DF).date()
                gap_first_second = (dep_date1 - dep_date2).days
                a = (gap_first_second / (period * 30))
                x = (value_residual - fal_dep / 12 * period * a)
                undone_dotation_number = int(x / y) + 1
                undone_dotation_number += 1

            res = undone_dotation_number
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    # completly override odoo method
    @api.one
    def asset_create(self):
        if self.asset_category_id and self.asset_category_id.method_number > 1:
            asset_start_date_format = datetime.strptime(
                self.asset_start_date, DF)
            quarters = rrule.rrule(
                rrule.MONTHLY, bymonth=(1, 4, 7, 10), bysetpos=-1,
                dtstart=datetime(asset_start_date_format.year, 1, 1),
                count=8)
            vals = {
                'name': self.name,
                'code': self.invoice_id.number or False,
                'category_id': self.asset_category_id.id,
                'value': self.price_subtotal,
                'partner_id': self.invoice_id.partner_id.id,
                'company_id': self.invoice_id.company_id.id,
                'currency_id': self.invoice_id.currency_id.id,
                'date': self.asset_start_date or self.invoice_id.date_invoice,
                'invoice_id': self.invoice_id.id,
                # hans change start in here
                'fal_purchase_date': self.asset_start_date,
                'fal_original_purchase_value': self.price_subtotal,
                'fal_second_depreciation_date':
                    quarters.after(asset_start_date_format)
                # end in here
            }
            asset_obj = self.env['account.asset.asset']
            category_id = vals['category_id']
            changed_vals = asset_obj.onchange_category_id_values(category_id)
            vals.update(changed_vals['value'])
            asset = self.env['account.asset.asset'].create(vals)
            if self.asset_category_id.open_asset:
                asset.validate()
        return True


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    fal_asset_ids = fields.One2many(
        'account.asset.asset', 'invoice_id', 'Assets')
    fal_asset_count = fields.Integer(
        compute='_compute_fal_asset_count', string='Asset Count')

    @api.multi
    def _compute_fal_asset_count(self):
        for invoice in self:
            invoice.fal_asset_count = len(invoice.fal_asset_ids)

    @api.multi
    def open_fal_asset(self):
        return {
            'name': _('Assets'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.asset.asset',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': dict(
                self.env.context or {}, search_default_invoice_id=self.id,
                default_invoice_id=self.id),
        }
