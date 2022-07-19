// Copyright (c) 2016-2022, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kundenbindung"] = {
    "filters": [
        {
            "fieldname":"customer_group",
            "label": __("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group"
        }
    ]
};
