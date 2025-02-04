// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item',  {
    refresh: function(frm) {
        if (!cur_frm.doc.__islocal) {
            frm.add_custom_button(__("French Attributes"),  function(){
              set_french_attributes(frm);
            });
            
            add_nextcloud_button(frm);
        }
    },
    packaging_type: function(frm) {
        set_french_packaging_type(frm);
    }
});

function set_french_attributes(frm) {
    frappe.call({
        'method': 'seg.seg.utils.set_french_attributes',
        'args': {
            'self': frm.doc.name,
            'event': "button"
        },
        'callback': function(response) {
            show_alert('Französische Attribute wurden gesetzt!', 3);
            cur_frm.reload_doc();
        }
    });
}

function set_french_packaging_type(frm) {
    if (frm.doc.packaging_type == "Karton") {
        cur_frm.set_value("packaging_type_fr", "Carton");
    } else if (frm.doc.packaging_type == "Palette") {
        cur_frm.set_value("packaging_type_fr", "Palette");
    }
}
