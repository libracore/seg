frappe.listview_settings['Sales Invoice'] = {
    onload: function(listview) {
        frappe.route_options.status = ["!=", "Cancelled"];
    }
};
