from openerp import api, models, _
from openerp.exceptions import UserError


class FalMultiConfirmAssetWizard(models.TransientModel):
    _name = "fal.multi.confirm.asset.wizard"

    @api.multi
    def action_confirm(self):
        if self.env.context.get('active_ids', False):
            asset_obj = self.env['account.asset.asset']
            active_ids = self.env.context.get('active_ids', False)
            asset_ids = asset_obj.browse(active_ids)
            asset_not_draft = asset_ids.filtered(lambda r: r.state != 'draft')
            if asset_not_draft:
                raise UserError(_('Asset should be in draft to confirmed it!'))
            for asset_id in asset_ids:
                asset_id.validate()
        return {'type': 'ir.actions.act_window_close'}
