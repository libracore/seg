frappe.listview_settings['Delivery Note'] = {
    onload: function(listview) {
        frappe.route_options.status = ["!=", "Cancelled"];
    }
};
