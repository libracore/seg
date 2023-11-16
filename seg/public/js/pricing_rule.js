frappe.ui.form.on('Pricing Rule', {
    after_save: function(frm) {
        check_pricing_rule_conflicts(frm)
    }
})

function check_pricing_rule_conflicts(frm) {
    frappe.call({
        'method': "seg.seg.pricing_rule_validation.validate_pricing_rule",
        'args': {
            'new_pr_name': frm.doc.name,
        },
        'callback': function (response) {}
    });
}
