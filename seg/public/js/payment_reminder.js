// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Reminder',  {
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
    },
    customer: function(frm) {
        if (!frm.doc.__islocal) {
            set_sales_person(frm);
        }
    }
});

frappe.ui.form.on('Payment Reminder Invoice',  {
    //Calculate new Total Amounts when Invoice is deleted
    sales_invoices_remove: function(frm) {
        let new_amount = 0
        if (frm.doc.sales_invoices && frm.doc.sales_invoices.length > 0) {
            for (let i = 0; i < frm.doc.sales_invoices.length; i++) {
                new_amount += frm.doc.sales_invoices[i].outstanding_amount;
            }
        }
        if (new_amount > 0) {
            cur_frm.set_value("total_before_charge", new_amount);
        } else {
            cur_frm.set_value("total_before_charge", 0);
        }
    }
});

function set_sales_person(frm) {
    if (frm.doc.customer) {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Customer",
                'name': frm.doc.customer
            },
            'callback': function(response) {
                var sales_person = response.message.customer_group;
                if (sales_person) {
                    frm.set_value("sales_person", sales_person);
                }
            }
        });
    } else {
        frm.set_value("sales_person", null);
    }
}
