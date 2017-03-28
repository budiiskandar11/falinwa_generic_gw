# -*- coding: utf-8 -*-
{
    "name": "Product - Coffee",
    "version": "1.0",
    'author': 'Falinwa Budi',
    "description": """
    Add information spesific for Tire
    """,
    "summary" : "Price for Product",
    "depends" : [
        'product','fleet', 'sales_team'
        ],
    'init_xml': [],
    'update_xml': [
        'views/product_view.xml',
        'views/fleet_model_menu.xml',
    ],
    'css': [],
    'js' : [],
    'installable': True,
    'active': False,
    'application' : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   