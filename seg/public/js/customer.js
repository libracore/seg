frappe.ui.form.on('Customer',  {
    refresh: function(frm) {
        display_email_invoice(frm);
    },
	mahnsperre: function(frm) {
		check_mahnsperre_on_invoices(frm);
	},
    email_invoices: function(frm) {
        if (frm.doc.email_invoices) {
            cur_frm.set_df_property('preferred_invoice_email', 'reqd', 1);
        } else {
            cur_frm.set_df_property('preferred_invoice_email', 'reqd', 0);
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

function display_email_invoice(frm) {
    if (frm.doc.email_invoices) {
        cur_frm.set_df_property('preferred_invoice_email', 'reqd', 1);
        cur_frm.dashboard.add_comment( "Kunde hat Emailrechnungsversand!<br>" + frm.doc.preferred_invoice_email, 'red', true);
    }
}
