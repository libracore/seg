// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt
let updating_fields = false;

frappe.ui.form.on('Quotation Price List', {
    refresh: function(frm) {
        //Autoset Sales Person
        if (cur_frm.doc.__islocal) {
            cur_frm.set_value("sales_person", frappe.session.user);
        } else {
            cur_frm.set_df_property('customer','read_only', true);
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
        
        //Filter Addresses
       frm.set_query('customer_address', function() {
            return {
                filters: {
                    'link_name': frm.doc.customer
                }
            };
        });
        
       frm.set_query('shipping_address_name', function() {
            return {
                filters: {
                    'link_name': frm.doc.customer
                }
            };
        });
        
        //Filter Customers
       frm.set_query('customer', function() {
            return {
                filters: {
                    'customer_group': frm.doc.customer_group
                }
            };
        });
        
        frm.add_custom_button(__("Reset Items"),  function(){
          reset_items(frm);
        });
        
    },
    before_save: function(frm) {
        set_items(frm);
    },
    contact: function(frm) {
        display_contact(frm);
    },
    customer: function(frm) {
        //Remove Contact, Addresses and Customer Name if Customer is changed
        cur_frm.set_value("customer_address", null);
        cur_frm.set_value("shipping_address_name", null);
        cur_frm.set_value("contact", null);
        if (!frm.doc.customer) {
            cur_frm.set_value("customer_name", null);
        } else {
            //Set Primary Address
            set_address(frm);
        }
    },
    customer_address: function(frm) {
        display_address(frm.doc.customer_address, "address_display");
    },
    shipping_address_name: function(frm) {
        display_address(frm.doc.shipping_address_name, "shipping_address");
    },
    sales_person: function(frm) {
        set_customer_group(frm.doc.sales_person);
    }
});

frappe.ui.form.on('Quotation Price List Templates', {
    before_templates_remove(frm, cdt, cdn) {
        let template_row = frappe.get_doc(cdt, cdn);
        //Remove Items releated to template
        remove_items(frm, template_row.item_code);
        frm.refresh_field('items');
    }
});

frappe.ui.form.on('Quotation Price List Items', {
    item_price(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        recalculate_prices(row, "item_price");
    },
    discount(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        recalculate_prices(row, "discount");
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
                for (let i = 0; i < response.message.new_items.length; i++) {
                    var child = cur_frm.add_child('items');
                    frappe.model.set_value(child.doctype, child.name, 'price_list_rate', response.message.new_items[i].price_list_rate);
                    frappe.model.set_value(child.doctype, child.name, 'item_code', response.message.new_items[i].item_code);
                    frappe.model.set_value(child.doctype, child.name, 'variant_of', response.message.new_items[i].variant_of);
                    frappe.model.set_value(child.doctype, child.name, 'item_price', response.message.new_items[i].item_price);
                    frappe.model.set_value(child.doctype, child.name, 'kg_price', response.message.new_items[i].kg_price);
                    frappe.model.set_value(child.doctype, child.name, 'discount', response.message.new_items[i].discount);
                    frappe.model.set_value(child.doctype, child.name, 'variant', response.message.new_items[i].variant);
                    frappe.model.set_value(child.doctype, child.name, 'variant_fr', response.message.new_items[i].variant_fr);
                    let row = frappe.get_doc(child.doctype, child.name);
                    if (row.kg_price) {
                        calculate_kg_and_l(row);
                    }
                }
                
                //mark imported templates
                for (let j = 0; j < response.message.imported_templates.length; j++) {
                    frappe.model.set_value("Quotation Price List Templates", response.message.imported_templates[j], "items_set", 1);
                }
            } else {
                frappe.show_alert('Keine neuen Artikel importiert', 3);
            }
        }
    });
}

function recalculate_prices(row, trigger) {
    if (!updating_fields) {
        //Calculate Item Price
        updating_fields = true
        if (trigger == "item_price") {
            let discount = 100 - (row.item_price * 100 / row.price_list_rate)
            frappe.model.set_value(row.doctype, row.name, "discount", discount).then(() => {
                updating_fields = false
            });
            if (row.kg_price) {
                calculate_kg_and_l(row);
            }
        }
        
        if (trigger == "discount") {
            let item_price = row.price_list_rate - (row.price_list_rate * row.discount / 100)
            frappe.model.set_value(row.doctype, row.name, "item_price", item_price).then(() => {
                updating_fields = false
            });
            if (row.kg_price) {
                calculate_kg_and_l(row);
            }
        }
    }
}

function calculate_kg_and_l(row) {
    frappe.call({
        'method': 'seg.seg.doctype.quotation_price_list.quotation_price_list.get_kg_and_l_price',
        'args': {
            'row': row
        },
        'callback': function(response) {
            if (response.message) {
                frappe.model.set_value(row.doctype, row.name, "item_price_l", response.message.liter_price);
                frappe.model.set_value(row.doctype, row.name, "item_price_kg", response.message.kg_price);
            }
        }
    });
}

function display_address(address, target_field) {
    if (address) {
        frappe.call({
            method: 'frappe.contacts.doctype.address.address.get_address_display',
            args: {
                address_dict: address
            },
            callback: function(response) {
                if (response.message) {
                    cur_frm.set_value(target_field, response.message);
                }
            }
        });
    } else {
       cur_frm.set_value(target_field, null);
    }
}

function set_address(frm) {
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Address",
            filters: {
                link_doctype: "Customer",
                link_name: cur_frm.doc.customer,
                address_type: "Billing",
                is_primary_address: 1
            },
            fields: ["name"]
        },
        callback: function(response) {
            if (response.message.length > 0) {
                cur_frm.set_value("customer_address", response.message[0].name);
            }
        }
    });
}

function set_customer_group(sales_person) {
    if (sales_person) {
        frappe.call({
            'method': 'seg.seg.doctype.quotation_price_list.quotation_price_list.get_customer_group',
            'args': {
                'user': sales_person
            },
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value("customer_group", response.message);
                } else {
                    cur_frm.set_value("customer_group", null);
                }
            }
        });
    } else {
        cur_frm.set_value("customer_group", null);
    }
}

function remove_items(frm, template) {
    for (let i = frm.doc.items.length -1; i >= 0; i--) {
        if (frm.doc.items[i].variant_of == template) {
            let items_row = frm.doc.items[i];
            frm.doc.items.splice(i, 1);
        }
    }
}

function reset_items(frm) {
    frm.clear_table('items');
    for (let i = 0; i < cur_frm.doc.templates.length; i++) {
        frappe.model.set_value(frm.doc.templates[i].doctype, frm.doc.templates[i].name, "items_set", 0);
    }
    
    //~ await set_items(frm);
    frm.refresh_field('items');
}
