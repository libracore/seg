frappe.ui.form.on('Sales Invoice',  {
	refresh: function(frm) {
		if (frm.doc.customer) {
			check_customer_mahnsperre(frm);
		} else {
			cur_frm.set_value("mahnsperre", 0);
		}
		
		if (frm.doc.is_return === 1) {
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
	frm.doc.items.forEach(function(item) {
        if (item.delivery_note) {
			frappe.call({
				"method": "frappe.client.get",
				"args": {
					"doctype": "Delivery Note",
					"name": item.delivery_note
				},
				'callback': function (response) {
					var dn = response.message;
					var dn_items = dn.items.length;
					var wir_percent = dn.wir_percent;
					var wir_on_returned_items = ((dn.wir_amount / dn_items) * frm.doc.items.length).toFixed(2);
					var return_wir_percent = ((wir_percent / dn_items) * frm.doc.items.length).toFixed(2);
					
					cur_frm.set_value("wir_amount", parseFloat(wir_on_returned_items));  
					frappe.model.set_value(item.doctype, item.name, "dn_wir", parseFloat(wir_on_returned_items));
					frappe.model.set_value(item.doctype, item.name, "wir_percent_on_return", parseFloat(return_wir_percent));
				}
			});
		}
    });
}
