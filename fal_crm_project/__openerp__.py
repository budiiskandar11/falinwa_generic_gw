# -*- coding: utf-8 -*-
{
    "name": "CRM Project Relationship",
    "version": "1.0",
    'author': 'Falinwa Hans',
    "description": """
    Module to add feature of CRM and Project
    """,
    "depends": [
        'base',
        'project',
        'crm',
        'fal_parent_account',
        'fal_crm_probability_ext',
        'crm_timesheet',
        'fal_activity_follow_up'
    ],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/crm_stage_data.xml',
        'data/salesteam_data.xml',
        'data/email_template.xml',
        'data/sequence.xml',
        'views/crm_lead_view.xml',
        'views/project_view.xml',
        'views/account_view.xml',
    ],
    'css': [],
    'js': [],
    'installable': True,
    'active': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
