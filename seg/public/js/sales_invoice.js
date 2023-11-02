frappe.ui.form.on('Sales Invoice',  {
	refresh: function(frm) {
		if (frm.doc.customer) {
			check_customer_mahnsperre(frm);
		} else {
			cur_frm.set_value("mahnsperre", 0);
		}
		if (frm.doc.is_return === 1 && frm.doc.wir_amount > 0) {
			update_wir_for_sinv_return(frm);
		}
	},
    before_save: function(frm) {
		if (frm.doc.mahnsperre === 1) {
			cur_frm.set_value("exclude_from_payment_reminder_until", "2099-12-31");
		} else if (frm.doc.is_return === 0) {
			// do not remind 20 days
			cur_frm.set_value("exclude_from_payment_reminder_until",frappe.datetime.add_days(frm.doc.due_date, 20));
		}
    }
});

function check_customer_mahnsperre(frm) {
	frappe.call({
		"method": "frappe.client.get",
		"args": {
			"doctype": "Customer",
			'name': frm.doc.customer
		},
		"callback": function(response) {
			var mahnsperre = response.message.mahnsperre;
			if (mahnsperre === 1) {
				cur_frm.set_value("mahnsperre", 1);
			} else {
				cur_frm.set_value("mahnsperre", 0);
			}
		}
	});
}

function update_wir_for_sinv_return(frm) {
	var return_wir_amount = 0;
	frm.doc.items.forEach(function(item) {
		return_wir_amount += item.wir_amount_on_item;
	});
	cur_frm.set_value("wir_amount", return_wir_amount);
}
