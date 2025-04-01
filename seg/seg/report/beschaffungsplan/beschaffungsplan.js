// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Beschaffungsplan"] = {
    "filters": [
        //~ {
            //~ "fieldname":"item_group",
            //~ "label": __("Item group"),
            //~ "fieldtype": "Link",
            //~ "options": "Item Group",
        //~ }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.id == "days_until_stock_ends") {
            var today = new Date();
            var stock_end = new Date(value);
            
            if (stock_end <= today) {
                value = "<span style='color:red;'>" + value + "</span>";
            } else {
                var daysDifference = frappe.datetime.get_day_diff(stock_end, today);
                console.log(daysDifference)
                if (daysDifference >= 1 && daysDifference <= 14) {
                    value = "<span style='color:orange;' >" + value + "</span>";
                } else {
                    value = "<span style='color:green;'>" + value + "</span>";
                }
            }
        
        }
        return value;
    },
};
