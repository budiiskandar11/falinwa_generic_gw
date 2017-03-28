# -*- coding: utf-8 -*-
{
    'name': 'ACC-31_Falinwa Account Asset Behaviour',
    'version': '1.1',
    'author': 'Falinwa Hans',
    'category': 'Accounting & Finance',
    'description': """
Module to give asset behaviour of Falinwa.
    """,
    'depends': ['account_asset'],
    'data': [
        'data/data.xml',
        'wizard/fal_multi_confirm_asset_wizard_view.xml',
        'views/account_asset.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
