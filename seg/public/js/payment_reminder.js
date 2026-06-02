// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Reminder',  {
    refresh: function(frm) {
        if (frm.doc.docstatus == 1) {
            // custom mail dialog
            cur_frm.page.add_action_icon("es-line-email", function() {
                custom_mail_dialog(frm);
            }, "", "Email");
            let target = $('span.menu-item-label').filter(function() {
                return $(this).text().trim() === __('Email');
            });
            $(target).parent().parent().remove();   // remove Menu > Email
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
