# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    number    = fields.Char(string="Asset Number")


    def _compute_board_amount(self, sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date):
        amount = 0
        if sequence == undone_dotation_number:
            amount = residual_amount
        else:
            if self.method == 'linear':
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
                if self.prorata:
                    amount = amount_to_depr / self.method_number
                    if sequence == 1:
                        if self.method_period % 12 != 0:
                            date = datetime.strptime(self.date, '%Y-%m-%d')
                            month_days = calendar.monthrange(date.year, date.month)[1]
                            days = month_days - date.day + 1
                            amount = (amount_to_depr / self.method_number) / month_days * days
                        else:
                            days = (self.company_id.compute_fiscalyear_dates(depreciation_date)['date_to'] - depreciation_date).days + 1
                            amount = (amount_to_depr / self.method_number) / total_days * days
            elif self.method == 'degressive':
                amount = residual_amount * self.method_progress_factor
                if self.prorata:
                    if sequence == 1:
                        if self.method_period % 12 != 0:
                            date = datetime.strptime(self.date, '%Y-%m-%d')
                            month_days = calendar.monthrange(date.year, date.month)[1]
                            days = month_days - date.day + 1
                            amount = (residual_amount * self.method_progress_factor) / month_days * days
                        else:
                            days = (self.company_id.compute_fiscalyear_dates(depreciation_date)['date_to'] - depreciation_date).days + 1
                            amount = (residual_amount * self.method_progress_factor) / total_days * days
        return amount

    def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
        undone_dotation_number = self.method_number
        if self.method_time == 'end':
            end_date = datetime.strptime(self.method_end, DF).date()
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = date(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+self.method_period)
                undone_dotation_number += 1
        if self.prorata:
            undone_dotation_number += 1
        return undone_dotation_number

    @api.multi
    def compute_depreciation_board(self):
        self.ensure_one()

        posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual
            if self.prorata:
                # if we already have some previous validated entries, starting date is last entry + method perio
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = datetime.strptime(self._get_last_depreciation_date()[self.id], DF).date()
            else:
                # depreciation_date = 1st of January of purchase year if annual valuation, 1st of
                # purchase month in other cases
                if self.method_period >= 12:
                    asset_date = datetime.strptime(self.date[:4] + '-01-01', DF).date()
                else:
                    asset_date = datetime.strptime(self.date[:7] + '-01', DF).date()
                    print "asssett", asset_date
                # if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = asset_date
                    print "xxxxx", depreciation_date
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            
            days_current_month = calendar.monthrange(year, month)[1]
            depreciation_date = datetime(depreciation_date.year, depreciation_date.month, days_current_month)

            undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)

            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                sequence = x + 1
                amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)
                amount = self.currency_id.round(amount)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount
                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': (self.code or '') + '/' + str(sequence),
                    'remaining_value': residual_amount,
                    'depreciated_value': self.value - (self.salvage_value + residual_amount),
                    'depreciation_date': depreciation_date.strftime(DF),
                }
                commands.append((0, False, vals))
                # Considering Depr. Period as months
                depreciation_date = date(year, month, day) + relativedelta(months=+self.method_period)
                depreciation_date = datetime(depreciation_date.year, depreciation_date.month, calendar.monthrange(depreciation_date.year, depreciation_date.month)[1])
                print"xxxx/", depreciation_date
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year

        self.write({'depreciation_line_ids': commands})
        return 

    @api.model
    def create(self, vals):
        seq_obj = self.env['ir.sequence']
        model = 'fal.account.asset.asset'
        vals['number'] = seq_obj.next_by_code(model) or 'New'
        return super(AccountAssetAsset, self).create(vals)
