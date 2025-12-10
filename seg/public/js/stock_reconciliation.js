// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Reconciliation', {
    refresh(frm) {
        if (frm.doc.docstatus == 0) {
            frm.add_custom_button(__("Get SEG Price"),  function(){
                get_seg_price(frm);
            });
        }
    }
});

function get_seg_price(frm) {
    frappe.call({
        'method': 'seg.seg.utils.get_seg_prices',
        'args': {
            'items': frm.doc.items
        },
        'callback': function(response) {
            if (response.message) {
                response.message.forEach(rowData => {
                    frappe.model.set_value("Stock Reconciliation Item", rowData.name, "valuation_rate", rowData.valuation_rate);
                });
                frm.refresh_field("items");
            } else {
                frappe.msgprint("Es ist ein Fehler beim abrufen der Preise aufgetreten.");
            }
        }
    });
}
