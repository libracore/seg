frappe.ui.form.on('Customer',  {
	mahnsperre: function(frm) {
		if (cur_frm.doc.customer_name){
			check_mahnsperre_on_invoices(frm);
		}
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
