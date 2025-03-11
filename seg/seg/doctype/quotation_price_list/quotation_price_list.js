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
    contact: function(frm) {
        display_contact(frm);
    },
    customer: function(frm) {
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
