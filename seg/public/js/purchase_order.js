// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order',  {
    refresh: function(frm) {
        //Set Taxes template
        if (frm.doc.__islocal) {
            set_taxes_template(frm);
        }
        
        if (frm.doc.docstatus == 1) {
            // custom mail dialog (prevent duplicate icons on creation)
            if (document.getElementsByClassName("fa-envelope-o").length === 0) {
                cur_frm.page.add_action_icon(__("fa fa-envelope-o"), function() {
                    custom_mail_dialog(frm);
                });
                var target ="span[data-label='" + __("Email") + "']";
                $(target).parent().parent().remove();   // remove Menu > Email
            }
        }
        
        //Filter drop Ship Reference
       frm.set_query('drop_ship_reference', function() {
            return {
                filters: {
                    'docstatus': 1
                }
            };
        });
    },
    validate: function(frm) {
        validate_order_recommendation(frm);
    },
    drop_ship_reference: function(frm) {
        set_drop_ship_address(frm);
    },
    supplier: function(frm) {
        set_taxes_template(frm);
    }
});

function set_drop_ship_address(frm) {
    if (frm.doc.drop_ship_reference) {
        frappe.call({
            'method': 'frappe.client.get',
            'args': {
                'doctype': "Delivery Note",
                'name': frm.doc.drop_ship_reference
            },
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value('drop_ship_address', response.message.shipping_address_name);
                    cur_frm.set_value('drop_ship_address_display', response.message.shipping_address);
                }
            }
        });
        //Set Items from Drop Ship Delivery Note
        set_dn_items(frm.doc.drop_ship_reference);
    } else {
        cur_frm.set_value("drop_ship_address", null);
        cur_frm.set_value("drop_ship_address_display", null);
        cur_frm.set_value("drop_ship_customer", null);
    }
}

function set_taxes_template(frm) {
    if (frm.doc.supplier) {
        frappe.call({
            'method': 'seg.seg.purchasing.get_taxes_template',
            'args': {
                'supplier': frm.doc.supplier
            },
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value("taxes_and_charges", response.message);
                } else {
                    cur_frm.set_value("taxes_and_charges", null);
                }
            }
        });
    } else {
        cur_frm.set_value("taxes_and_charges", null);
    }
}

function validate_order_recommendation(frm) {
    let affected_items = false;
    let message = "Folgende Artikelmenge liegen unter der Bestellempfehlung des Lieferanten:<br>"
    for (let i = 0; i < frm.doc.items.length; i++) {
        if (frm.doc.items[i].order_recommendation_supplier && frm.doc.items[i].order_recommendation_supplier > 0 && frm.doc.items[i].qty < frm.doc.items[i].order_recommendation_supplier) {
            message = message + "<br>" + frm.doc.items[i].item_code + ": " + frm.doc.items[i].item_name + " (Zeile " + frm.doc.items[i].idx + ")";
            affected_items = true
        }
    }
    
    if (affected_items) {
        frappe.msgprint(message, "Bestellempfehlung Lieferant");
    }
}

function set_dn_items(delivery_note) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Delivery Note",
            'name': delivery_note
        },
        'callback': function(response) {
            if (response.message) {
                cur_frm.clear_table("items");
                let dn_items = response.message.items;
                for (let i = 0; i < dn_items.length; i++) {
                    var child = cur_frm.add_child('items');
                    frappe.model.set_value(child.doctype, child.name, 'item_code', dn_items[i].item_code);
                    frappe.model.set_value(child.doctype, child.name, 'qty', dn_items[i].qty);
                }
                cur_frm.refresh_field("items");
                frappe.show_alert("Artikel aus Lieferschein wurden übernommen", 5);
            }
        }
    });
}
