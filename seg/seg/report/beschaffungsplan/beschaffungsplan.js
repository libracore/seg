// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Beschaffungsplan"] = {
    "filters": [
        {
            "fieldname":"days_until_stock_ends",
            "label": __("Stock End Date"),
            "fieldtype": "Date"
        }
    ],
    onload: function(report) {
        report.page.add_inner_button(__("Create Purchase Order"), function () {
            create_purchase_order(report);
        });
    }
};

function create_purchase_order(report) {
    let filters = report.get_values();
    frappe.prompt([
        {'fieldname': 'supplier', 'fieldtype': 'Link', 'options': 'Supplier', 'label': __('Supplier'), 'reqd': 1}  
    ],
    function(values){
        frappe.dom.freeze('Bitte warten, die Bestellung erzeugt...');
        frappe.call({
            'method': 'seg.seg.report.beschaffungsplan.beschaffungsplan.create_purchase_order',
            'args': {
                'supplier': values['supplier'],
                'filters': filters
            },
            'callback': function(response) {
                frappe.dom.unfreeze();
                if (response.message) {
                    window.open("desk#Form/Purchase Order/" + response.message, '_blank');
                } else {
                    frappe.show_alert('Fehler beim erstellen der Bestellung', 5);
                }
            }
        });
    },
    'Please Select Supplier',
    'Create'
    );
}
