# -*- coding: utf-8 -*-
{
    "name": "Fal Activity Follow Up",
    "version": "1.0",
    'author': 'Falinwa Randy',
    "description": """
    Generic Fal Activity Follow Up
    """,
    "depends": [
        'base',
        'project',
        'crm',
        'crm_timesheet',
    ],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
    ],
    'css': [],
    'js': [],
    'installable': True,
    'active': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
