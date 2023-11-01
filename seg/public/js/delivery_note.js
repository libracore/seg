frappe.ui.form.on('Delivery Note', {
    refresh(frm) {
        frm.add_custom_button(__("Umlagern"), function() {
            move_stock(frm);
        });
    },
    before_save: function(frm) {
		//calculate the wir_percent and wir_amount for each item
		if (frm.doc.wir_percent > 0) {
			update_wir_for_each_item(frm);
		}
		
		if (!frm.doc.ignore_pricing_rule) {
			cur_frm.set_value("keep_pricing_rule_for_all_items", 0);
			check_pricing_rule(frm);
		}
	},
    keep_pricing_rule_for_all_items (frm) {
		if (frm.doc.keep_pricing_rule_for_all_items == 1 && frm.doc.ignore_pricing_rule) {
			frappe.msgprint("Please unchecked 'Ignore Pricing Rule' and Save the document before enabling this.");
			cur_frm.set_value("keep_pricing_rule_for_all_items", 0);
		} 
		check_pricing_rule(frm);
		
	}
})

frappe.ui.form.on('Delivery Note Item', {
    keep_pricing_rule_rate_for_this_item: function(frm, cdt, cdn) {
        var item = locals[cdt][cdn];
        if (item.keep_pricing_rule_rate_for_this_item == 1 && frm.doc.ignore_pricing_rule) {
			frappe.msgprint("Please unchecked 'Ignore Pricing Rule' and Save the document before enabling this.");
			frappe.model.set_value(item.doctype, item.name, 'keep_pricing_rule_rate_for_this_item', 0);
		} 
        modify_item_rate(item);
    }
})

function check_pricing_rule(frm) {
	frm.doc.items.forEach(function (item) {
		frappe.model.set_value(item.doctype, item.name, 'keep_pricing_rule_rate_for_this_item', frm.doc.keep_pricing_rule_for_all_items);
		modify_item_rate(item);
	});
}

function modify_item_rate(item) {
	if (item.keep_pricing_rule_rate_for_this_item == 1){
		var price_rule_rate = item.rate;
		frappe.model.set_value(item.doctype, item.name, 'discount_percentage', 0);
		frappe.model.set_value(item.doctype, item.name, 'price_list_rate', price_rule_rate);
	} else {
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
	}
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
