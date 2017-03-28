from odoo import fields, models, api, _
import openerp.addons.decimal_precision as dp


class account_voucher(models.Model):
    _name = "account.voucher"
    _inherit = "account.voucher"

    @api.multi
    def _amount_all_hkd(self, field_name, arg):
        cur_obj = self.env['res.currency']
        res = {}
        context = dict(self._context)
        ctx = context.copy()
        for voucher in self:
            ctx.update({'date': voucher.date})
            rate_ids = cur_obj.search([('name', '=', 'HKD')], context=ctx, limit=1)
            temp = voucher.amount
            cur = voucher.currency_id
            for rate_id in cur_obj.browse(rate_ids, ctx):
                if cur != rate_id:
                    temp = cur_obj.compute(cur.id, rate_id.id, temp, context=ctx)
            res[voucher.id] = cur_obj.round(cur, temp)
        return res

    amount_total_hkd = fields.Float(
        compute='_amount_all_hkd',
        string='Total (HKD)',
        store=True,
        help="The total amount in HKD."
    )


# end of account_voucher()
