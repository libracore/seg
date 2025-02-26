// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order',  {
    refresh: function(frm) {
        //Set Taxes template
        if (frm.doc.__islocal) {
            set_taxes_template(frm);
        }
        
        if (frm.doc.docstatus == 1) {
            // custom mail dialog (prevent duplicate icons on creation)
            if (document.getElementsByClassName("fa-envelope-o").length === 0) {
                cur_frm.page.add_action_icon(__("fa fa-envelope-o"), function() {
                    custom_mail_dialog(frm);
                });
                var target ="span[data-label='" + __("Email") + "']";
                $(target).parent().parent().remove();   // remove Menu > Email
            }
        }
        
        //Filter drop Ship Reference
       frm.set_query('drop_ship_reference', function() {
            return {
                filters: {
                    'docstatus': 1
                }
            };
        });
    },
    drop_ship_reference: function(frm) {
        set_drop_ship_address(frm);
    },
    supplier: function(frm) {
        set_taxes_template(frm);
    }
});

function set_drop_ship_address(frm) {
    if (frm.doc.drop_ship_reference) {
        frappe.call({
            'method': 'frappe.client.get',
            'args': {
                'doctype': "Delivery Note",
                'name': frm.doc.drop_ship_reference
            },
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value('drop_ship_address', response.message.shipping_address_name);
                    cur_frm.set_value('drop_ship_address_display', response.message.shipping_address);
                }
            }
        });
    } else {
        cur_frm.set_value("drop_ship_address", null);
        cur_frm.set_value("drop_ship_address_display", null);
        cur_frm.set_value("drop_ship_customer", null);
    }
}

function set_taxes_template(frm) {
    if (frm.doc.supplier) {
        frappe.call({
            'method': 'seg.seg.purchasing.get_taxes_template',
            'args': {
                'supplier': frm.doc.supplier
            },
            'callback': function(response) {
                if (response.message) {
                    console.log(response.message);
                    cur_frm.set_value("taxes_and_charges", response.message);
                } else {
                    cur_frm.set_value("taxes_and_charges", null);
                }
            }
        });
    } else {
        cur_frm.set_value("taxes_and_charges", null);
    }
}


