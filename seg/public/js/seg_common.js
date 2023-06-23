// Copyright (c) 2021-2023, libracore AG and contributors
// For license information, please see license.txt
// Common functions

// 1 sec after start (has to be delayed after document ready)
window.onload = async function () {
    setTimeout(function() {
        if (window.location.toString().includes("/desk#modules/SEG")) {
            create_customized_menu();
            console.log("menu created");
        }
    }, 1000);
}

function create_customized_menu() {
    create_menu("create_sample_nic", "Musterbezug Nic", "6710 - Materialentnahme Nic - SEG");
    create_menu("create_sample_chris", "Musterbezug Christian", "6711 - Materialentnahme Christian - SEG");
    create_menu("create_sample_ben", "Musterbezug Beni", "6712 - Materialentnahme Beni - SEG");
}

function create_menu(endpoint, title, account) {
    var menu_entry_parent = $("a:contains('" + endpoint + "')").parent();
    menu_entry_parent.removeClass("flush-top");
    menu_entry_parent.html("");
    var menu_entry = $("<span class='indicator grey' data-v-32b346d7=''></span><span class='link_content' data-v-32b346d7='' href='/desk#modules/SEG'>" + title + "</span>");
    menu_entry.click(function () { 
        frappe.route_options = {"stock_entry_type": "Material Receipt"};
        locals.difference_account = account; 
        frappe.set_route("Form", "Stock Entry", "New Stock Entry");
    });
    menu_entry_parent.append(menu_entry);
}
