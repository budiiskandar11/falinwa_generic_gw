# -*- coding: utf-8 -*-
{
    "name": "Custom Partner for S3Mortar",
    "version": "1.0",
    'author': 'Databit Solusi Indonesia',
    "description": """
    Module to give partner sequence in reference field.
    """,
    "depends": ['base'],
    'init_xml': [],
    'update_xml': [
        'views/partner_sequence.xml',
        'views/partner_view_inherit.xml',
    ],
    'css': [],
    'js': [
    ],
    'installable': True,
    'active': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
