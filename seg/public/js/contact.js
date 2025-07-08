// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt


frappe.ui.form.on('Contact',  {
    before_save: function(frm) {
        if (frm.doc.links && frm.doc.links.length > 0) {
            set_link_title_and_company(frm);
        } else if (frm.doc.company_name) {
            cur_frm.set_value("company_name", null);
        }
    }
});

function set_link_title_and_company(frm) {
    if (cur_frm.doc.__islocal) {
        for (let i = 0; i < frm.doc.links.length; i++) {
            if (frm.doc.links[i].link_doctype == "Customer" || frm.doc.links[i].link_doctype == "Supplier" || frm.doc.links[i].link_doctype == "Lead") {
                let field = frm.doc.links[i].link_doctype.toLowerCase() + "_name";
                frappe.call({
                    'method': "frappe.client.get_value",
                    'args': {
                        'doctype': frm.doc.links[i].link_doctype,
                        'filters': {'name': frm.doc.links[i].link_name},
                        'fieldname': field,
                        'as_dict': false
                    },
                    'callback': function(response) {
                        if (response.message) {
                            frappe.model.set_value(frm.doc.links[i].doctype, frm.doc.links[i].name, "link_title", response.message[field]);
                            if (i == 0) {
                                cur_frm.set_value("company_name", frm.doc.links[0].link_title);
                            }
                        }
                    }
                });
            }
        }
    } else {
        cur_frm.set_value("company_name", frm.doc.links[0].link_title);
    }
}

