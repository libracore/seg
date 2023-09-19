frappe.ui.form.on('Sales Invoice',  {
    before_save: function(frm) {
		setTimeout(function () {  
			if (frm.doc.mahnsperre === 1) {
				cur_frm.set_value("exclude_from_payment_reminder_until", "2099-12-31");
			} else if (frm.doc.is_return === 0) {
				// do not remind 20 days
				cur_frm.set_value("exclude_from_payment_reminder_until",frappe.datetime.add_days(frm.doc.due_date, 20));
			}
        }, 800);
                            
    }
});
