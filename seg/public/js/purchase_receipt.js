// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Receipt',  {
    refresh: function(frm) {
        cache_seg_settings(frm);
    },
    onload: function(frm) {
        if (frm.doc.__islocal && frm.doc.items[0].item_code) {
            //Set Freight costs, Currency exchange fees, SEG Purchase Price
            set_seg_price(frm);
        }
    },
    on_submit: function(frm) {
        //Update SEG Price in all affected Items
        if (!frm.doc.exclude_from_seg_price) {
            update_item_seg_price(frm, "submit");
        }
    },
    after_cancel: function(frm) {
        //Update SEG Price in all affected Items
        if (!frm.doc.exclude_from_seg_price) {
            update_item_seg_price(frm, "cancel");
        }
    },
    before_save: function(frm) {
        //Calcualte SEG Total and create Taxes Entry for freight costs and Exchange Fees
        calculate_seg_total(frm);
    },
});

frappe.ui.form.on('Purchase Receipt Item',  {
    freight_costs: function(frm, cdt, cdn) {
        update_seg_price(frm, cdt, cdn);
    },
    rate: function(frm, cdt, cdn) {
        update_seg_price(frm, cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
        update_seg_price(frm, cdt, cdn);
    }
});

function set_seg_price(frm) {
    frappe.dom.freeze('Bitte warten, SEG Preise werden berechnet...');
    frappe.call({
        'method': 'seg.seg.purchasing.get_updated_seg_prices',
        'args': {
            'items': frm.doc.items,
            'price_list': frm.doc.buying_price_list
        },
        'callback': function(response) {
            if (response.message) {
                cur_frm.doc.items = response.message;
                cur_frm.save()
                frappe.dom.unfreeze();
            } else {
                frappe.show_alert({message:__("Fehler beim Laden der Frachtkosten und Währungsspesen"), indicator:'red'});
                frappe.dom.unfreeze();
            }
        }
    });
}

function update_item_seg_price(frm, event) {
    frappe.call({
        'method': 'seg.seg.purchasing.update_item_seg_price',
        'args': {
            'items': frm.doc.items,
            'event': event
        }
    });
}

function update_seg_price(frm, cdt, cdn) {
    var item = locals[cdt][cdn];
    var result = item.rate + (item.rate / 100 * item.currency_exchange_fees) + item.freight_costs
    item.seg_purchase_price = result;
    item.seg_amount = result * item.qty;
    cur_frm.refresh_field('items');
}

function calculate_seg_total(frm) {
    if (locals.seg_settings) {
        let seg_settings = locals.seg_settings;
        //Get Totals
        let total = 0;
        let freight_costs = 0;
        let exchange_fees = 0;
        for (let i = 0; i < frm.doc.items.length; i++) {
            total += frm.doc.items[i].seg_amount;
            freight_costs += frm.doc.items[i].freight_costs * frm.doc.items[i].qty;
            exchange_fees += (frm.doc.items[i].amount / 100) * frm.doc.items[i].currency_exchange_fees
        }
        //Set Seg Total
        cur_frm.set_value("seg_total", total);
        
        //Remove old Taxes Entries
        for (let j = frm.doc.taxes.length - 1; j >= 0; j--) {
            if (frm.doc.taxes[j].freight_exchange) {
                frappe.model.clear_doc(frm.doc.taxes[j].doctype, frm.doc.taxes[j].name);
            }
        }
        
        //Add new Rows
        if (freight_costs > 0) {
            let freight_child = cur_frm.add_child('taxes');
            frappe.model.set_value(freight_child.doctype, freight_child.name, 'charge_type', "Actual");
            frappe.model.set_value(freight_child.doctype, freight_child.name, 'account_head', seg_settings.freight_account);
            frappe.model.set_value(freight_child.doctype, freight_child.name, 'tax_amount', freight_costs);
            frappe.model.set_value(freight_child.doctype, freight_child.name, 'description', seg_settings.freight_description);
            frappe.model.set_value(freight_child.doctype, freight_child.name, 'freight_exchange', 1);
        }
        
        if (exchange_fees > 0) {
            let exchange_child = cur_frm.add_child('taxes');
            frappe.model.set_value(exchange_child.doctype, exchange_child.name, 'charge_type', "Actual");
            frappe.model.set_value(exchange_child.doctype, exchange_child.name, 'account_head', seg_settings.exchange_account);
            frappe.model.set_value(exchange_child.doctype, exchange_child.name, 'tax_amount', exchange_fees);
            frappe.model.set_value(exchange_child.doctype, exchange_child.name, 'description', seg_settings.exchange_description);
            frappe.model.set_value(exchange_child.doctype, exchange_child.name, 'freight_exchange', 1);
        }
    }
}

function cache_seg_settings(frm) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "SEG Settings",
            'name': "SEG Settings"
        },
        'callback': function(response) {
            if (response.message) {
                locals.seg_settings = response.message;
            }
        }
    });
}
