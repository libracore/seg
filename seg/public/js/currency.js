// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Currency',  {
    before_save: function(frm) {
        //Update Item Prices, if Currency exchange fee has been changed
        update_item_prices(frm);
    }
});

function update_item_prices(frm) {
    if (frm.doc.name != "CHF") {
        frappe.call({
            "method": "seg.seg.utils.update_item_prices",
            "args": {
                'currency': frm.doc.name,
                'currency_exchange_fee': frm.doc.currency_exchange_fee
            }
        });
    }
}
