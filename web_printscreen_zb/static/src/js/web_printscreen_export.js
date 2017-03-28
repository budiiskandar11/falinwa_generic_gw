odoo.define('web_printscreen_zb.web_printscreen_export', function(require) {
'use strict';

    var core = require('web.core');    
    var _t = core._t;
    var ListView = require('web.ListView');
    var TreeView = require('web.TreeView');
    var formats = require('web.formats');
    var ViewManager = require('web.ViewManager');
    
    ListView.include({
        load_list: function (data, grouped) {
            var self = this;
            var links = document.getElementsByClassName("oe_list_button_import_excel");
            var links_pdf = document.getElementsByClassName("oe_list_button_import_pdf");
            if (links && links[0]){
                links[0].onclick = function() {
                    self.export_to_excel("excel");
                };
            }
            if (links_pdf && links_pdf[0]){
                links_pdf[0].onclick = function() {
                    self.export_to_excel("pdf");
                };
            }  
            return this._super.apply(this, arguments);
        },
        export_to_excel: function(export_type) {
            var self = this;
            var export_type = export_type;
            var view = this.getParent();
            // Find Header Element
            var header_eles = self.$el.find('.o_list_view > thead > tr');
            var header_name_list = [];
            //console.log('header_eles:', header_eles);
            $.each(header_eles,function(){
                var $header_ele = $(this);
                var header_td_elements = $header_ele.find('th');
                //console.log('header_td_elements:', header_td_elements);
                $.each(header_td_elements,function(){
                    var $header_td = $(this);
                    var text = $header_td.text().trim() || "";
                    var data_id = $header_td.attr('data-id');
                    if (text && !data_id){
                        data_id = 'group_name';
                    }
                    header_name_list.push({'header_name': text.trim(), 'header_data_id': data_id});
                   // }
                });
            });
            
            //console.log('header:', header_name_list);
            
            //Find Data Element
            var data_eles = self.$el.find('.o_list_view > tbody > tr');
            //console.log('data_eles:', data_eles);
            var export_data = [];
            $.each(data_eles,function(){
                var data = [];
                var $data_ele = $(this);
                var is_analysis = false;
                if ($data_ele.text().trim()){
                //Find group name
                    var group_th_eles = $data_ele.find('th');
                    $.each(group_th_eles,function(){
                        var $group_th_ele = $(this);
                        var text = $group_th_ele.text();
                        var is_analysis = true;
                        data.push({'data': text, 'bold': true});
                    });
                    var data_td_eles = $data_ele.find('td');
                    $.each(data_td_eles,function(){
                        var $data_td_ele = $(this);
                        var text = $data_td_ele.text().trim() || "";
                        if ($data_td_ele && $data_td_ele[0].classList.contains('oe_number') && !$data_td_ele[0].classList.contains('oe_list_field_float_time')){
                            text = text.replace('%', '');
                            text = formats.parse_value(text, { type:"float" });
                            data.push({'data': text || "", 'number': true});
                        }
                        else{
                            data.push({'data': text});
                        }
                    });
                    export_data.push(data);
                }
            });
            //console.log('export_data:', export_data);
            //Find Footer Element
            
            var footer_eles = self.$el.find('.o_list_view > tfoot> tr');
            $.each(footer_eles,function(){
                var data = [];
                var $footer_ele = $(this);
                var footer_td_eles = $footer_ele.find('td');
                $.each(footer_td_eles,function(){
                    var $footer_td_ele = $(this);
                    var text = $footer_td_ele.text().trim() || "";
                    if ($footer_td_ele && $footer_td_ele[0].classList.contains('oe_number')){
                        text = formats.parse_value(text, { type:"float" });
                        data.push({'data': text || "", 'bold': true, 'number': true});
                    }
                    else{
                        data.push({'data': text, 'bold': true});
                    }
                });
                export_data.push(data);
            });
            //console.log('export_dataf:', export_data);
            //Export to excel
            $.blockUI();
            if (export_type === 'excel'){
                 view.session.get_file({
                     url: '/web/export/zb_excel_export',
                     data: {data: JSON.stringify({
                            model : view.process_model,
                            headers : header_name_list,
                            rows : export_data,
                     })},
                     complete: $.unblockUI
                 });
             }
             else{
                new instance.web.Model("res.users").get_func("read")(this.session.uid, ["company_id"]).then(function(res) {
                    new instance.web.Model("res.company").get_func("read")(res['company_id'][0], ["name"]).then(function(result) {
                        view.session.get_file({
                             url: '/web/export/zb_pdf_export',
                             data: {data: JSON.stringify({
                                    uid: view.session.uid,
                                    model : view.process_model,
                                    headers : header_name_list,
                                    rows : export_data,
                                    company_name: result['name']
                             })},
                             complete: $.unblockUI
                         });
                    });
                });
             }
        },
    });
    
    TreeView.include({
        load_tree: function () {
            var self = this;
            this._super.apply(this, arguments);
            var links = document.getElementsByClassName("oe_list_button_import_excel");
            var links_pdf = document.getElementsByClassName("oe_list_button_import_pdf");
            $.each(links,function(){
                $(this)[0].onclick = function() {
                    self.export_to_excel("excel")
                };
            })
            $.each(links_pdf,function(){
                $(this)[0].onclick = function() {
                    self.export_to_excel("pdf")
                };
            })
        },
        export_to_excel: function(export_type) {
            var self = this
            var export_type = export_type
            view = this.getParent()
            // Find Header Element
            header_eles = self.$el.find('.treeview-header')
            header_name_list = []
            $.each(header_eles,function(){
                $header_td = $(this)
                text = $header_td.text().trim() || ""
                data_id = $header_td.attr('data-id')
                if (text && !data_id){
                    data_id = 'group_name'
                }
                header_name_list.push({'header_name': text.trim(), 'header_data_id': data_id})
            });
            
            //Find Data Element
            data_eles = self.$el.find('.oe-treeview-table > tbody > tr')
            export_data = []
            $.each(data_eles,function(){
                data = []
                $data_ele = $(this)
                is_analysis = false
                if ($data_ele.text().trim()){
                //Find group name
                    group_th_eles = $data_ele.find('th')
                    $.each(group_th_eles,function(){
                        $group_th_ele = $(this)
                        text = $group_th_ele.text()
                        is_analysis = true
                        data.push({'data': text, 'bold': true})
                    });
                    data_td_eles = $data_ele.find('td')
                    $.each(data_td_eles,function(){
                        $data_td_ele = $(this)
                        text = $data_td_ele.text().trim() || ""
                        if ($data_td_ele && $data_td_ele[0].classList.contains('oe_number') && !$data_td_ele[0].classList.contains('oe_list_field_float_time')){
                            text = text.replace('%', '')
                            text = instance.web.parse_value(text, { type:"float" })
                            data.push({'data': text || "", 'number': true})
                        }
                        else{
                            data.push({'data': text})
                        }
                    });
                    export_data.push(data)
                }
            });
            
            //Find Footer Element
            
            footer_eles = self.$el.find('.oe_list_content > tfoot> tr')
            $.each(footer_eles,function(){
                data = []
                $footer_ele = $(this)
                footer_td_eles = $footer_ele.find('td')
                $.each(footer_td_eles,function(){
                    $footer_td_ele = $(this)
                    text = $footer_td_ele.text().trim() || ""
                    if ($footer_td_ele && $footer_td_ele[0].classList.contains('oe_number')){
                        text = instance.web.parse_value(text, { type:"float" })
                        data.push({'data': text || "", 'bold': true, 'number': true})
                    }
                    else{
                        data.push({'data': text, 'bold': true})
                    }
                });
                export_data.push(data)
            });
            //Export to excel
            $.blockUI();
            if (export_type === 'excel'){
                 view.session.get_file({
                     url: '/web/export/zb_excel_export',
                     data: {data: JSON.stringify({
                            model : view.process_model,
                            headers : header_name_list,
                            rows : export_data,
                     })},
                     complete: $.unblockUI
                 });
             }
             else{
                new instance.web.Model("res.users").get_func("read")(this.session.uid, ["company_id"]).then(function(res) {
                    new instance.web.Model("res.company").get_func("read")(res['company_id'][0], ["name"]).then(function(result) {
                        view.session.get_file({
                             url: '/web/export/zb_pdf_export',
                             data: {data: JSON.stringify({
                                    uid: view.session.uid,
                                    model : view.process_model,
                                    headers : header_name_list,
                                    rows : export_data,
                                    company_name: result['name']
                             })},
                             complete: $.unblockUI
                         });
                    });
                });
             }
        },
    });
    
    ViewManager.include({

        switch_mode: function (view_type, no_store, options) {
            if(view_type != 'list'){
                $('.oe_list_button_import_excel').hide();
            }else{
                $('.oe_list_button_import_excel').show();
            }
            return this._super.apply(this, arguments);
        }, 

    });
});
