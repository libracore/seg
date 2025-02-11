// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer',  {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            add_nextcloud_button(frm);
        }
    }
});
