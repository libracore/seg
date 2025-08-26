frappe.listview_settings['Quotation'] = {
    onload: function(listview) {
        frappe.route_options.status = ["!=", "Cancelled"];
    }
};
