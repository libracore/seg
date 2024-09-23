frappe.ui.form.on('Customer',  {
	setup: function(frm){
		set_allow_invoice(frm);
	},
	mahnsperre: function(frm) {
		check_mahnsperre_on_invoices(frm);
	}
});

function check_mahnsperre_on_invoices(frm) {
	frappe.call({
		"method": "seg.seg.mahnsperre.set_mahnsperre",
		"args": {
			"customer": frm.doc.name,
			"mahnsperre": frm.doc.mahnsperre,
		},
		"callback": function(response) {
			console.log("Exclude From Payment Reminder Until Updated");
		}
	});
}

function set_allow_invoice(frm){
	frappe.call({
		"method": "seg.seg.customer.set_allow_invoice",
		"args": {
			"customer": frm.doc.name,
			"allow_invoice": 1,
		},
		"callback": function(response) {
		}
	});
}
