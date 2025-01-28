// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer',  {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            add_nextcloud_button(frm);
        }
    },
    mahnsperre: function(frm) {
        check_mahnsperre_on_invoices(frm);
    }
});

function check_mahnsperre_on_invoices(frm) {
    frappe.call({
        "method": "seg.seg.mahnsperre.set_mahnsperre",
        "args": {
            "customer": frm.doc.name,
            "mahnsperre": frm.doc.mahnsperre,
        },
        "callback": function(response) {
            console.log("Exclude From Payment Reminder Until Updated");
        }
    });
}
