# -*- coding: utf-8 -*-
{
    "name": "Stock Card ",
    "version": "1.0",
    'author': 'Databit Solusi Indonesia',
    "description": """
    Kartu Stock
    """,
    "depends": ['stock'],
    'init_xml': [],
    'update_xml': [
        "view/stock_sequence.xml",
        "view/menu.xml", 
        "view/stock_card.xml", 
        "view/stock_summary.xml",
        "report/stock_card.xml",
       # "data/ir_sequence.xml",
        #"security/ir.model.access.csv",
    ],
    'css': [],
    'js': [
    ],
    'installable': True,
    'active': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
