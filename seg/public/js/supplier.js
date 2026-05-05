// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier',  {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            add_nextcloud_button(frm);
        }
        
        if (frm.doc.has_skonto) {
            //Display a Comment if Skonto is avalaiable for this Supplier
            display_skonto_comment(frm);
        }
    }
});

function display_skonto_comment(frm) {
    let message;
    if (frm.doc.skonto_note) {
        message = "Bei diesem Lieferanten ist Skonto verfügbar: " + frm.doc.skonto_note
    } else {
        message = "Bei diesem Lieferanten ist Skonto verfügbar."
    }
    cur_frm.dashboard.add_comment(message, 'red', true);
}
