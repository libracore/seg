// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

var flag = 0;
frappe.ui.form.on('Delivery Note', {
    refresh(frm) {
        display_purchase_price_field(frm);
        
        if (frm.doc.docstatus == 0) {
            frm.add_custom_button(__("Update Barcodes"), function() {
                //Update Barcode, if they have changed in item meanwhile
                update_barcodes(frm);
            });
        }
        
        frm.add_custom_button(__("Umlagern"), function() {
            move_stock(frm);
        });
        if (!frm.doc.ignore_pricing_rule) {
            frm.add_custom_button(__("Detach From Pricing Rule"), function() {
                modify_item_rate(frm);
            });
        }
        if (frm.doc.is_return === 1) {
			remind_of_discount(frm);
		}
        //Set picked up if customer is marked as "always picks up"
        if (cur_frm.doc.__islocal) {
            set_only_samples_properties(frm);
            if (frm.doc.customer) {
                check_pick_up(frm.doc.customer);
                //~ display_dn_note(frm.doc.customer);
            } else {
                cur_frm.set_value("picked_up" , 0)
            }
        } else {
            add_dn_nextcloud_button(frm);
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
    
        if ((frm.doc.docstatus === 1) && (cur_frm.attachments.get_attachments().length === 0)) {
            frm.add_custom_button(__("PDF"), function() {
                attach_pdf(frm);
            });
        }
    },
    before_save: function(frm) {
        if (frm.doc.only_samples == 1) {
            var taxes = cur_frm.doc.taxes;
            if (taxes.length > 0) {
                taxes.forEach(function(entry) {
                    /* enter VOC target account here */
                    if (entry.account_head.startsWith("2208 ")) {
                        frappe.model.set_value("Sales Taxes and Charges", 
                        entry.name, 'tax_amount', 0);
                    } 
                });
            }
        } else {
            // update VOC
            update_voc(frm);
        }
        
        //Set Rates for Sample Sales Order
        set_sample_rates(frm);
        
        // calculate wir amount from percent
        update_wir(frm);
        //calculate the wir_percent and wir_amount for each item
        if (frm.doc.wir_percent > 0) {
            update_wir_for_each_item(frm);
        }
    },
    ignore_pricing_rule: function(frm) {
        // When unchecking the "Ignore Pricing Rule" after "Deatch Prices" the rate with the rule remains so this will bring back the original selling rate
        if (!frm.doc.ignore_pricing_rule) {
            return_to_previous_rate(frm);
        } 
    },
    customer: function(frm) {
        if (frm.doc.customer) {
            check_pick_up(frm.doc.customer);
            display_dn_note(frm.doc.customer);
        } else {
            cur_frm.set_value("picked_up" , 0)
        }
    },
    validate: function(frm) {
      // write delivery reference into the items to trace them later
        // loop through items
        frm.doc.items.forEach(function(entry) {
            frappe.model.set_value("Delivery Note Item", entry.name, 'delivery_reference', frm.doc.name);
            frappe.model.set_value("Delivery Note Item", entry.name, 'picked_up', frm.doc.picked_up);
        });
	
        if (frm.doc.picked_up == 1 || frm.doc.only_samples == 1) {
            frm.doc.taxes.forEach(function(entry) {
                if (entry.account_head == "2209 Geschuldete LSVA - SEG") {
                    frappe.model.set_value("Sales Taxes and Charges", entry.name, 'tax_amount', 0);
                } 
            });
        } else {
            getTotalWeight();
        }
        
        check_alternative_items(frm);
    },
    wir_percent: function(frm) {
        update_wir(frm);
    },
    on_submit: function(frm) {
        attach_pdf(frm);
        //Update considered qty in items for SEG Purchase Price
        update_item(frm, "submit");
    },
    after_cancel: function(frm) {
        update_item(frm, "cancel");
    },
    only_samples: function(frm) {
        if (frm.doc.__islocal && frm.doc.only_samples) {
            cur_frm.set_value("only_samples", 0);
        } else if (!frm.doc.only_samples) {
            cur_frm.set_value("ignore_pricing_rule", 0);
        }
    }
    /*onload: function(frm) {
        if (flag === 0) {
            cur_frm.set_value("ignore_pricing_rule", 0);
            flag = 1;
        }
    },*/
})

//~ frappe.ui.form.on('Delivery Note Item', {
    //~ item_code(frm, cdt, cdn) {
        //~ display_pruchase_price_field(frm, cdt, cdn);
    //~ }
//~ })


function modify_item_rate(frm) {
    frm.doc.items.forEach(function (item) {
        var price_rule_rate = item.rate;
        frappe.model.set_value(item.doctype, item.name, 'discount_percentage', 0);
        frappe.model.set_value(item.doctype, item.name, 'price_list_rate', price_rule_rate);
    });
    cur_frm.set_value("ignore_pricing_rule", 1);
}

function return_to_previous_rate(frm){
    frm.doc.items.forEach(function (item) {
        frappe.call({
            "method": "frappe.client.get",
            "args": {
                "doctype": "Item Price",
                "filters": {
                    "item_code": item.item_code,
                    "selling": 1
                }
            },
            "callback": function(response) {
                if (response) {
                    var item_price_list_rate = response.message.price_list_rate;
                    frappe.model.set_value(item.doctype, item.name, 'price_list_rate', item_price_list_rate);
                }
            }
        });
    });
}

function move_stock(frm) {
    var items = [];
    frm.doc.items.forEach(function (item) {
        if (!items.includes(item.item_code)) {
            items.push(item.item_code);
        }
    });
    var d = new frappe.ui.Dialog({
        'fields': [   
            {
                'fieldname': 'target_item', 
                'fieldtype': 'Link', 
                'label': __('Zielartikel'), 
                'options': "Item", 
                'reqd': 1,
                'get_query': function() { 
                    return { 
                        'filters': [['item_code', 'IN', items]]
                    } 
                },
                'onchange': function() {
                    // get qty from this position
                    frm.doc.items.forEach(function (item) {
                        if (item.item_code === d.fields_dict.target_item.value) {
                            console.log(item.qty);
                            d.set_value("qty", item.qty);
                        }
                    });
                }
            },
            {
                'fieldname': 'source_item', 
                'fieldtype': 'Link', 
                'label': __('Quellartikel'), 
                'options': "Item", 
                'reqd': 1, 
                'description': 'Dieser Artikel muss Alterantiven aktiviert haben und alternative Artikel haben',
                'get_query': function() { 
                    return { 
                        'query': 'seg.seg.filters.get_alternative_items',
                        'filters': {'item_code': d.fields_dict.target_item.value } 
                    } 
                }
            },
            {
                'fieldname': 'warehouse', 
                'fieldtype': 'Link', 
                'label': __('Warehouse'), 
                'options': "Warehouse", 
                'reqd': 1,
                'default': (frm.doc.items[0].warehouse)
            },
            {
                'fieldname': 'qty', 
                'fieldtype': 'Float', 
                'label': __('Qty'), 
                'default': 1, 
                'reqd': 1
            }
        ],
        'primary_action': function() {
            d.hide();
            var values = d.get_values();
            // convert material
            frappe.call({
                "method": "seg.seg.utils.convert_material",
                "args": {
                    "source_item": values.source_item,
                    "target_item": values.target_item,
                    "warehouse": values.warehouse,
                    "qty": values.qty
                },
                "callback": function(response) {
                    frappe.msgprint( "Umgelagert" );
                }
            });
        },
        'primary_action_label': __('Umlagern')
    });
    d.show();
}

function update_wir_for_each_item(frm) {
    frm.doc.items.forEach(function(item) {
        frappe.model.set_value("Delivery Note Item", item.name, "wir_percent_on_item", (frm.doc.wir_percent / frm.doc.items.length));
        frappe.model.set_value("Delivery Note Item", item.name, "wir_amount_on_item", (frm.doc.wir_amount * (item.net_amount / frm.doc.net_total)));
   });
}

function remind_of_discount(frm) {
    frappe.call({
        'method': "seg.seg.utils.check_dn_discount",
        'args': {
            'delivery_note': frm.doc.return_against
        },
        'callback': function(response) {
            var discount = response.message;
            if (discount) {
                cur_frm.dashboard.add_comment( "Achtung: Lieferschein " + frm.doc.return_against + " hat CHF " + discount + " Rabatt", 'red', true);
            }
        }
    });
}

function display_purchase_price_field(frm) {
    frappe.call({
        'method': 'frappe.client.get',
        'args': {
            'doctype': "SEG Settings",
            'name': "SEG Settings"
        },
        'callback': function(response) {
            if (response.message) {
               cur_frm.fields_dict['items'].grid.grid_rows.forEach((grid_row)=> {
                    grid_row.docfields.forEach((df)=>{
                        if (df.fieldname == "purchase_price") {
                            df.depends_on = `eval:doc.item_code == "${response.message.free_text_item}"`;
                            df.reqd = 1;
                        }
                    });
                });
                cur_frm.refresh_field('items');
            }
        }
    });
}

// mutation observer for item changes
var totalObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
 	    getTotalWeight();
    });
});
var target=document.querySelector('div[data-fieldname="total"] .control-input-wrapper .control-value');
var options = {
    attributes: true,
    characterData: true
};
totalObserver.observe(target, options);

function update_wir(frm) {
    if (frm.doc.wir_percent > 0) {
        cur_frm.set_value("wir_amount", frm.doc.net_total * (frm.doc.wir_percent / 100));
    }
}

function attach_pdf(frm) {
    frappe.call({
        'method': 'erpnextswiss.erpnextswiss.attach_pdf.attach_pdf',
        'args': {
            'doctype': frm.doc.doctype,
            'docname': frm.doc.name,
            'print_format': "Lieferschein",
            'background': 0,
            'hashname': 1,
            'is_private': 0
        },
        'callback': function(response) {
            cur_frm.reload_doc();
        }
    });
}

// this function will cache the nextcloud path and create a "Cloud" button
function add_dn_nextcloud_button(frm) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "SEG Settings",
            "name": "SEG Settings"
        },
        "callback": function(response) {
            let settings = response.message;
            if (settings.nextcloud_enabled) {
                if (frappe.user.has_role("Accounts Manager")) {
                    // elevated cloud menu
                    locals.cloud_url = settings.cloud_hostname 
                        + "/apps/files/?dir=/" 
                        + settings.storage_folder
                        + "/" + "Customer"
                        + "/" + (frm.doc.customer.replaceAll("/", "_"));
                    frm.add_custom_button(__("Gemeinsam"), function() {
                        window.open(locals.cloud_url, '_blank').focus();
                    }, __("Cloud"));

                    locals.restricted_cloud_url = settings.cloud_hostname 
                        + "/apps/files/?dir=/" 
                        + settings.restricted_storage_folder
                        + "/" + "Customer"
                        + "/" + (frm.doc.customer.replaceAll("/", "_"));
                    frm.add_custom_button(__("Eingeschränkt"), function() {
                        window.open(locals.restricted_cloud_url, '_blank').focus();
                    }, __("Cloud"));
                } else {
                    // simple cloud menu
                    locals.cloud_url = settings.cloud_hostname 
                        + "/apps/files/?dir=/" 
                        + settings.storage_folder
                        + "/" + "Customer"
                        + "/" + (frm.doc.customer.replaceAll("/", "_"));
                    frm.add_custom_button(__("Cloud"), function() {
                        window.open(locals.cloud_url, '_blank').focus();
                    }).addClass("btn-primary");
                }
            }
        }
    });
}

function display_dn_note(customer) {
    frappe.call({
        'method': "frappe.client.get_list",
        'args':{
            'doctype': "Customer",
            'filters': [
                ["name","IN", [cur_frm.doc.customer]]
            ],
            'fields': ["leave_delivery_note_note", "delivery_note_note"]
        },
        'callback': function (r) {
            var customer = r.message[0];
            
            if (customer.leave_delivery_note_note === 1) {
                frappe.msgprint({
                    title: __('Auf diesem Kunden ist ein Vermerk hinterlegt:'),
                    indicator: 'red',
                    message: __(` &nbsp;  &nbsp; ${ customer.delivery_note_note }`)
                });
            }
        }
    });
}

function update_barcodes(frm) {
    frappe.call({
        'method': 'seg.seg.delivery.check_barcodes',
        'args': {
            'doc': frm.doc
        },
        'callback': function(response) {
            if (response.message) {
                let new_barcodes = response.message;
                let removed_barcodes = "";
                for (let i = 0; i < new_barcodes.length; i++) {
                    if (!new_barcodes[i].barcode) {
                        removed_barcodes = removed_barcodes + "<br>" +  new_barcodes[i].item_code;
                    } else {
                        frappe.model.set_value("Delivery Note Item", new_barcodes[i].line_name, "barcode", new_barcodes[i].barcode);
                    }
                }
                frappe.show_alert("Barcodes wurden aktualisiert", 3);
                if (removed_barcodes.length > 0) {
                    frappe.msgprint("Folgende Artikel müssen manuell bearbeitet werden, da der Barcode komplett entfernt wurde <br>" + removed_barcodes);
                }
            }
        }
    });
}

//Check if purchase Items have an alternative, otherwise show pop-up
function check_alternative_items(frm) {
    frappe.call({
        'method': 'seg.seg.delivery.check_alternative_items',
        'args': {
            'items': frm.doc.items
        }
    });
}

function update_item(frm, event) {
    frappe.call({
        'method': 'seg.seg.purchasing.update_considered_qty',
        'args': {
            'items': frm.doc.items,
            'event': event
        }
    });
}

function set_sample_rates(frm) {
    if (frm.doc.only_samples) {
        cur_frm.set_value("ignore_pricing_rule", 1);
        for (let i = 0; i < frm.doc.items.length; i++) {
            if (!frm.doc.items[i].original_rate_set) {
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate", frm.doc.items[i].rate);
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate_set", 1);
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "discount_percentage", 100);
            }
        }
    } else {
        for (let i = 0; i < frm.doc.items.length; i++) {
            if (frm.doc.items[i].original_rate_set) {
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "rate", frm.doc.items[i].original_rate);
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate_set", 0);
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate", 0);
            }
        }
    }
}

function set_only_samples_properties(frm) {
    cur_frm.set_df_property('only_samples','description',"Kann nach dem ersten speichern gesetzt werden.");
}
