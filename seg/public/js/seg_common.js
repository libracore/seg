// Copyright (c) 2021-2025, libracore AG and contributors
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
        frappe.route_options = {"stock_entry_type": "Material Issue"};
        locals.difference_account = account; 
        var target = "New Stock Entry";
        if (frappe.boot.lang === "de") {
            target = "Neu Lagerbuchung";
        }
        frappe.set_route("Form", "Stock Entry", target);
    });
    menu_entry_parent.append(menu_entry);
}

// this function will cache the nextcloud path and create a "Cloud" button
function add_nextcloud_button(frm) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "SEG Settings",
            "name": "SEG Settings"
        },
        "callback": function(response) {
            let settings = response.message;
            if (settings.nextcloud_enabled) {
                if (frappe.user.has_role("Accounts Manager")) {
                    // elevated cloud menu
                    locals.cloud_url = settings.cloud_hostname 
                        + "/apps/files/?dir=/" 
                        + settings.storage_folder
                        + "/" + frm.doc.doctype
                        + "/" + (frm.doc.name.replaceAll("/", "_"));
                    frm.add_custom_button(__("Gemeinsam"), function() {
                        window.open(locals.cloud_url, '_blank').focus();
                    }, __("Cloud"));

                    locals.restricted_cloud_url = settings.cloud_hostname 
                        + "/apps/files/?dir=/" 
                        + settings.restricted_storage_folder
                        + "/" + frm.doc.doctype
                        + "/" + (frm.doc.name.replaceAll("/", "_"));
                    frm.add_custom_button(__("Eingeschränkt"), function() {
                        window.open(locals.restricted_cloud_url, '_blank').focus();
                    }, __("Cloud"));
                } else {
                    // simple cloud menu
                    locals.cloud_url = settings.cloud_hostname 
                        + "/apps/files/?dir=/" 
                        + settings.storage_folder
                        + "/" + frm.doc.doctype
                        + "/" + (frm.doc.name.replaceAll("/", "_"));
                    frm.add_custom_button(__("Cloud"), function() {
                        window.open(locals.cloud_url, '_blank').focus();
                    }).addClass("btn-primary");
                }
            }
        }
    });
}

function custom_mail_dialog(frm) {
    frappe.call({
        'method': 'seg.seg.utils.get_email_recipient_and_message',
        'args': {
            'doc': frm.doc
        },
        'callback': function(response) {
            var recipient = response.message.recipient || cur_frm.doc.contact_email;
            var subject = response.message.subject
            var message = response.message.message
            new frappe.views.CommunicationComposer({
                doc: {
                    doctype: cur_frm.doc.doctype,
                    name: cur_frm.doc.name
                },
                subject: subject,
                //~ cc:  cc,
                //~ bcc: bcc,
                recipients: recipient,
                attach_document_print: true,
                message: message
            });
            setTimeout(function () {
                // attach VLA file
                var checkboxes = $('input[type="checkbox"]');
                for (var i = 0; i < checkboxes.length; i++) { 
                    //~ if (checkboxes[i].labels[0].innerHTML.indexOf(".pdf") > 0
                        console.log(checkboxes[i].labels[0]);
                        checkboxes[i].checked = true;
                    //~ }
                }
            }, 500);
        }
    });
}

function check_pick_up(customer) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Customer",
            'name': customer
        },
        'callback': function(response) {
            if (response.message.always_pick_up) {
                cur_frm.set_value("picked_up" , 1);
            } else {
                cur_frm.set_value("picked_up" , 0);
            }
        }
    });
}

function update_voc(frm) {
    /* enter LSVA tax rate here */
    var voc_amount = 0;
    frm.doc.items.forEach(function(item) {
        if (item.voc) {
            voc_amount += item.qty * item.voc;
        } 
    });
    
    var taxes = cur_frm.doc.taxes;
    if (taxes.length > 0) {
        taxes.forEach(function(entry) {
            /* enter VOC target account here */
            if (entry.account_head.startsWith("2208 ")) {
                frappe.model.set_value("Sales Taxes and Charges", 
                entry.name, 'tax_amount', voc_amount);
            } 
        });
    }
}

// trigger to calculate total weight
function getTotalWeight() {
    if ((cur_frm.doc.docstatus === 0) && (cur_frm.doc.items)) {
        var item_codes = [];
        var qtys = [];
        cur_frm.doc.items.forEach(function(entry) {
            if (entry.item_code !== null) {
                item_codes.push(entry.item_code);
                qtys.push(entry.qty);
            } 
        });
        frappe.call({
            'method': 'seg.seg.utils.get_total_weight',
            'args': { 
                'items': item_codes,
                'qtys': qtys 
            },
            'async': false,
            'callback': function(r) {
                if (!r.exc) {
                    updateWeight(r.message.total_weight);
                    updateLSVA(r.message.total_weight);
                }
            }
        });
    }
}

function updateWeight(totalWeight) {
    cur_frm.set_value("total_weight", totalWeight);
}

function updateLSVA(totalWeight) {
    /* enter LSVA tax rate here */
    //var taxAmount = totalWeight * 0.07;
    var taxAmount = (Math.round(9 * totalWeight / 10)) / 10;        /* 2023-03-22 updated from 7 to 9 by request Anna */
    var taxes = cur_frm.doc.taxes;
    if (taxes.length > 0) {
        taxes.forEach(function(entry) {
            /* enter LSVA target account here */
            if (entry.account_head.startsWith("2209 ")) {
                frappe.model.set_value("Sales Taxes and Charges", 
                entry.name, 'tax_amount', taxAmount);
            }
        });
    }
}
