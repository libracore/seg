frappe.listview_settings['Payment Reminder'] = {
    onload: function(listview) {
        frappe.route_options.docstatus = ["!=", 2];
    }
};
