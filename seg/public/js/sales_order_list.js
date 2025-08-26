frappe.listview_settings['Sales Order'] = {
    onload: function(listview) {
        frappe.route_options.status = ["!=", "Cancelled"];
    }
};
