# -*- coding: utf-8 -*-
{
    "name": "Product - Karung",
    "version": "1.0",
    'author': 'Falinwa Budi',
    "description": """
    Add information spesific for Karung
    """,
    "summary" : "karung for Product",
    "depends" : [
        'product','sale',
        ],
    'init_xml': [],
    'update_xml': [
        'views/product_view.xml',
        'views/sale_inherit_view.xml',
    ],
    'css': [],
    'js' : [],
    'installable': True,
    'active': False,
    'application' : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   