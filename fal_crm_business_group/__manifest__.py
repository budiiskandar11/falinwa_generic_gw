# -*- coding: utf-8 -*-
{
    'name': 'CRM:  Business Group',
    'version': '1.0',
    'author': 'Falinwa Indonesia',
    'description': '''
    This module has features:\n
    1. Add business group\n
    ''',
    'depends': [
        'crm',
        'sales_team',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fal_business_group_view.xml',
    ],
    'css': [],
    'js': [],
    'installable': True,
    'active': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
