# -*- coding: utf-8 -*-
{
    "name": "GEN-08_Total Amount HKD Store",
    "version": "1.0",
    'author': 'Falinwa Hans',
    "description": """
    Module to customize Total amount in HKD for all the views and report (order / invoice). (Store Version)
    """,
    "depends": [
        'base',
        'purchase',
        'sale',
        #'account',
        #'account_voucher',
        #'purchase_discount'
    ],
    'init_xml': [],
    'update_xml': [
        'views/purchase_view.xml',
        # 'views/sale_view.xml',
        # 'views/account_invoice_view.xml',
        # 'views/account_voucher_view.xml',
    ],
    'css': [],
    'installable': True,
    'active': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
