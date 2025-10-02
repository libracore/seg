// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Receipt',  {
    onload: function(frm) {
        if (frm.doc.__islocal && frm.doc.items[0].item_code) {
            //Set Freight costs, Currency exchange fees, SEG Purchase Price
            console.log("peace");
            set_seg_price(frm);
        }
    },
    on_submit: function(frm) {
        //Update SEG Price in all affected Items
        update_item_seg_price(frm, "submit");
    },
    after_cancel: function(frm) {
        //Update SEG Price in all affected Items
        update_item_seg_price(frm, "cancel");
    }
});

frappe.ui.form.on('Purchase Receipt Item',  {
    freight_costs: function(frm, cdt, cdn) {
        update_seg_price(frm, cdt, cdn);
    },
    rate: function(frm, cdt, cdn) {
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
    cur_frm.refresh_field('items');
}
