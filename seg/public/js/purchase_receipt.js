// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Receipt',  {
    onload: function(frm) {
        //Set Taxes template
        if (frm.doc.__islocal) {
            //Set Freight costs, Currency exchange fees, SEG Purchase Price
            set_seg_price(frm);
        }
    },
    on_submit: function(frm) {
        //Update SEG Price in all affected Items
        update_item_seg_price(frm);
    },
    after_cancel: function(frm) {
        //Update SEG Price in all affected Items
        update_item_seg_price(frm);
    }
});

function set_seg_price(frm) {
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
            } else {
                frappe.show_alert({message:__("Fehler beim Laden der Frachtkosten und Währungsspesen"), indicator:'red'});
            }
        }
    });
}

function update_item_seg_price(frm) {
    frappe.call({
        'method': 'seg.seg.purchasing.update_item_seg_price',
        'args': {
            'items': frm.doc.items
        }
    });
}
