frappe.ui.form.on('Delivery Note', {
    refresh(frm) {
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
        //Set picked up uf customer is marked as "always picks up"
        if (cur_frm.doc.__islocal) {
            check_pick_up(frm);
        }
    },
    before_save: function(frm) {
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
        check_pick_up(frm);
    }
})

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

function check_pick_up(frm) {
    if (frm.doc.customer) {
        
    } else {
        cur_frm.set_value("picked_up" , 0)
    }
}
