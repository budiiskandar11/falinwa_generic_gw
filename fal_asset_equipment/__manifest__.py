# -*- coding: utf-8 -*-

{
    'name': 'Asset - Equipments',
    'version': '1.0',
    'sequence': 125,
    'author': 'Falinwa Budi',
    'category' : 'Accounting',
    'description': """
        Bridge between Asset and Equipment.""",
    'depends': ['account_asset','maintenance'],
    'summary': 'Equipments, Assets, Internal Hardware, Allocation Tracking',
    'data': [
        'data/sequence.xml',
        #'security/equipment.xml',
        'views/maintenance_views.xml',
        'views/asset_view_inherit.xml',

    ],
    'demo': [],
    'installable': True,
    'auto-install': True,
}
