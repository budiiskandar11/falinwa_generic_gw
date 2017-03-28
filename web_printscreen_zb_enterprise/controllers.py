# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

try:
    import json
except ImportError:
    import simplejson as json
from openerp import http as openerpweb
from openerp.addons.web.controllers.main import ExcelExport
from openerp.addons.web.controllers.main import Export
import re
from cStringIO import StringIO
from lxml  import etree
import trml2pdf
import time, os
import locale
import openerp.tools as tools
try:
    import xlwt
except ImportError:
    xlwt = None

import openerp.http as http
from openerp.http import request

class ZbExcelExport(ExcelExport):
    #_cp_path = '/web/export/zb_excel_export'

    def zb_from_data(self, fields, rows):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        style = xlwt.easyxf('align: wrap yes')
        font = xlwt.Font()
        font.bold = True
        style.font = font
        ignore_index = []
        count = 0
        for i, fieldname in enumerate(fields):
            #if fieldname.get('header_data_id', False):
            field_name = fieldname.get('header_name', '')
            worksheet.write(0, i-count, field_name, style)
            worksheet.col(i).width = 8000
            #else:
            #    count += 1
            #    ignore_index.append(i)
        style = xlwt.easyxf('align: wrap yes')
        bold_style = xlwt.easyxf('align: wrap yes')
        font = xlwt.Font()
        font.bold = True
        bold_style.font = font
        for row_index, row in enumerate(rows):
            count = 0
            for cell_index, cell_value in enumerate(row):
                #if cell_index not in ignore_index:
                cell_style = style
                if cell_value.get('bold', False):
                    cell_style = bold_style
                cellvalue = cell_value.get('data', '')
                if isinstance(cellvalue, basestring):
                    cellvalue = re.sub("\r", " ", cellvalue)
                if cell_value.get('number', False) and cellvalue:
                    cellvalue = float(cellvalue)
                if cellvalue is False: cellvalue = None
                worksheet.write(row_index + 1, cell_index - count, cellvalue, cell_style)
                #else:
                #    count += 1
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
    
    @http.route('/web/export/zb_excel_export', type='http', auth='user')
    def export_xls_view(self, req, data, token):
        data = json.loads(data)
        return req.make_response(
            self.zb_from_data(data.get('headers', []), data.get('rows', [])),
                           headers=[
                                    ('Content-Disposition', 'attachment; filename="%s.xls"'
                                        % data.get('model', 'Export')),
                                    ('Content-Type', self.content_type)
                                    ],
                                 cookies={'fileToken': token}
                                 )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: