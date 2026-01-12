frappe.ui.form.on('Pricing Rule', {
    after_save: function(frm) {
        check_pricing_rule_conflicts(frm);
    },
    discount_calculation: function(frm) {
        if (frm.doc.discount_calculation > 0) {
            //Calculate Discount Percentage for target Price
            calculate_discount_percentage(frm);
        }
    }
})

function check_pricing_rule_conflicts(frm) {
    frappe.call({
        'method': "seg.seg.pricing_rule_validation.validate_pricing_rule",
        'args': {
            'new_pr_name': frm.doc.name
        },
    });
}

function calculate_discount_percentage(frm) {
    if (frm.doc.items && frm.doc.items.length > 0) {
        frappe.call({
            'method': 'seg.seg.utils.get_discount_percentage',
            'args': {
                'item': frm.doc.items[0].item_code,
                'discounted_rate': frm.doc.discount_calculation,
                'currency': frm.doc.currency
            },
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value('discount_percentage', response.message);
                    cur_frm.set_value('discount_calculation', 0);
                } else {
                    frappe.msgprint("Der Prozentsatz konnte nicht abgerufen werden");
                }
            }
        });
    } else {
        frappe.msgprint("Bitte zuerst den Artikel definieren");
    }
}
