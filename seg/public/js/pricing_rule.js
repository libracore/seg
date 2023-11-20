frappe.ui.form.on('Pricing Rule', {
    after_save: function(frm) {
        check_pricing_rule_conflicts(frm);
    }
})

function check_pricing_rule_conflicts(frm) {
	console.log("apply_on", frm.doc.apply_on)
    frappe.call({
        'method': "seg.seg.pricing_rule_validation.validate_pricing_rule",
        'args': {
            'new_pr_name': frm.doc.name,
            'apply_on': frm.doc.apply_on
        },
        'callback': function (response) {}
    });
}
