frappe.ui.form.on('Customer',  {
	mahnsperre: function(frm) {
		check_mahnsperre_on_invoices(frm);
	}
});

function check_mahnsperre_on_invoices(frm) {
	frappe.call({
		"method": "seg.seg.mahnsperre.set_mahnsperre",
		"args": {
			"mahnsperre": frm.doc.mahnsperre,
            "customer": frm.doc.name,
		},
		"callback": function(response) {
			console.log("Exclude From Payment Reminder Until Updated");
		}
	});
}
