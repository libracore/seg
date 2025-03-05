// Copyright (c) 2016, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Open Purchase Orders"] = {
    "filters": [
        {
            "fieldname":"only_overdue",
            "label": __("Only Overdue Orders"),
            "fieldtype": "Check",
            "default": 1
        }
    ]
};
