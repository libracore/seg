frappe.ui.form.on('Delivery Note', {
    refresh(frm) {
        frm.add_custom_button(__("Umlagern"), function() {
            move_stock(frm);
        });
    }
})

function move_stock(frm) {
    var d = new frappe.ui.Dialog({
        'fields': [   
            {'fieldname': 'source_item', 'fieldtype': 'Link', 'label': __('Quellartikel'), 'options': "Item", 'reqd': 1, 'description': 'Dieser Artikel muss Alterantiven aktiviert haben und alternative Artikel haben'},
            {'fieldname': 'target_item', 'fieldtype': 'Link', 'label': __('Zielartikel'), 'options': "Item", 'reqd': 1,
                'get_query': function() { 
                    return { 
                        'query': 'seg.seg.filters.get_alternative_items',
                        'filters': {'item_code': d.fields_dict.source_item.value } 
                    } 
                }
            },
            {'fieldname': 'warehouse', 'fieldtype': 'Link', 'label': __('Warehouse'), 'options': "Warehouse", 'reqd': 1},
            {'fieldname': 'qty', 'fieldtype': 'Float', 'label': __('Qty'), 'default': 1, 'reqd': 1 }
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
