// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quotation Price List', {
    refresh: function(frm) {
        //Autoset Sales Person
        if (cur_frm.doc.__islocal) {
            cur_frm.set_value("sales_person", frappe.session.user);
        }
        //Filter Sales Person
        frm.set_query('sales_person', function() {
            return {
                filters: {
                    'link_doctype': 'User',
                    'user_type': "System User"
                }
            };
        });
        //Filter Contacts
       frm.set_query('contact', function() {
            return {
                filters: {
                    'link_name': frm.doc.customer
                }
            };
        });
        //Filter templates
        frm.fields_dict["templates"].grid.get_field("item_code").get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    "variant_of": ""
                }
            };
        };
    },
    before_save: function(frm) {
        set_items(frm);
    },
    contact: function(frm) {
        display_contact(frm);
    },
    customer: function(frm) {
        //Remove Contact and Customer Name if Customer is changed
        cur_frm.set_value("contact", null);
        if (!frm.doc.customer) {
            cur_frm.set_value("customer_name", null);
        }
    }
});

function display_contact(frm) {
    if (frm.doc.contact) {
       frappe.call({
           method: 'frappe.contacts.doctype.contact.contact.get_contact_details',
           args: {
               contact: frm.doc.contact
           },
           callback: function(response) {
               if (response.message) {
                   let contact_display = response.message.contact_display
                   if (response.message.contact_phone) {
                       contact_display = contact_display + "<br>" + response.message.contact_phone;
                   }
                   if (response.message.contact_mobile) {
                       contact_display = contact_display + "<br>" + response.message.contact_mobile;
                   }
                   if (response.message.contact_email) {
                       contact_display = contact_display + "<br>" + response.message.contact_email;
                   }
                   frm.set_value('contact_display', contact_display);
               }
           }
       });
   } else {
       cur_frm.set_value("contact_display", null);
    }
}

function set_items(frm) {
    frappe.call({
        'method': 'seg.seg.doctype.quotation_price_list.quotation_price_list.get_new_items',
        'args': {
            'doc': frm.doc
        },
        'callback': function(response) {
            if (response.message.something_to_import) {
                //create new items
                for (let i = 0; response.message.new_items.length; i++) {
                    var child = cur_frm.add_child('items');
                    frappe.model.set_value(child.doctype, child.name, 'item_code', response.message.new_items[i].item_code);
                    frappe.model.set_value(child.doctype, child.name, 'item_price', response.message.new_items[i].item_price);
                }
                
                //mark imported templates
                for (let j = 0; response.message.imported_templates.length; j++) {
                    frappe.model.set_value("Quotation Price List Templates", response.message.imported_templates[j], "items_set", 1);
                }
            } else {
                show_alert('Keine neuen Artikel importiert', 3);
            }
        }
    });
}
