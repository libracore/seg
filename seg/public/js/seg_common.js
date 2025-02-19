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
        }
    });
}
