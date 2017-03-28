# -*- coding: utf-8 -*-
{
    "name": "Manufacturing by Machine/Equipment",
    "version": "1.0",
    'author': 'Falinwa Budi',
    "description": """
    Add manufacturing by machine
    """,
    "summary" : "Machine Work Order",
    "depends" : [
        'mrp',
        ],
    'init_xml': [],
    'update_xml': [
        'views/work_order_sequence.xml',
        'views/mrp_production_inherit.xml',
        #'views/project_view.xml',
    ],
    'css': [],
    'js' : [],
    'installable': True,
    'active': False,
    'application' : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   