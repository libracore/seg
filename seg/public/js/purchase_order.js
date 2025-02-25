// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order',  {
    refresh: function(frm) {
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
