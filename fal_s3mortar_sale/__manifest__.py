# -*- coding: utf-8 -*-
{
    "name": "Sales Custom for S3Mortar",
    "version": "1.0",
    'author': 'Falinwa Indonesia',
    "description": """
    Change view for Indonesia
    """,
    "depends": ['sale','sales_team','dos_amount_to_text_id','account'],
    'init_xml': [],
    'update_xml': [
        'views/sale_view.xml',
        'views/sale_package.xml',
        'views/sale_agent.xml',
    ],
    'css': [],
    'js': [
    ],
    'installable': True,
    'active': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
