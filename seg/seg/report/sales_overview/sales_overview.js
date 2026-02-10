// Copyright (c) 2016, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Overview"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": (function() {
                                let year = frappe.datetime.get_today().split("-")[0];
                                return year + "-01-01";
                            })(),
            "reqd": 1
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname":"employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Sales Overview Employee"
        },
        {
            "fieldname":"depth",
            "label": __("Depth"),
            "fieldtype": "Select",
            "options": "Item Group\nProduct Group\nProduct Subcategory\nProduct Category\nGeneral"
        }
    ]
};
