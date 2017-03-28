# -*- encoding: utf-8 -*-

{
    'name': 'Web Printscreen Master',
    'version': '1.0',
    'category': 'Web',
    'description': """
        Module to export current active tree view in to excel report.
        Ported from Web Printscreen MW to be compatible for enterprise version.
    """,
    'author': 'Manexware S.A. & Falinwa Limited',
    'website': 'http://www.falinwa.com',
    'depends': ['web'],
    'data': ['views/web_printscreen_mw.xml'],
    'qweb': ['static/src/xml/web_printscreen_export.xml'],
    'installable': True,
    'auto_install': False,
    'web_preload': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
