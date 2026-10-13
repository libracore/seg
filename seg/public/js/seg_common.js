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
                message: message,
                frm: cur_frm,
                attach_document_print: true,
            });
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

function modify_item_rate(frm) {
    frm.doc.items.forEach(function (item) {
        var price_rule_rate = item.rate;
        frappe.model.set_value(item.doctype, item.name, 'discount_percentage', 0);
        frappe.model.set_value(item.doctype, item.name, 'price_list_rate', price_rule_rate);
    });
    cur_frm.set_value("ignore_pricing_rule", 1);
}

function update_wir(frm) {
    if (!frm.doc.set_manual_wir_amount) {
        cur_frm.set_value("wir_amount", frm.doc.net_total * (frm.doc.wir_percent / 100));
    }
}

function set_fixed_wir_percentage(frm) {
    if (frm.doc.customer) {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Customer",
                'name': frm.doc.customer
            },
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value("wir_percent", response.message.fixed_wir_share);
                }
            }
        });
    } else {
        cur_frm.set_value("wir_percent", 0);
    }
}

function toggle_wir_amount(frm, refresh=false) {
    if (!frm.doc.set_manual_wir_amount) {
        cur_frm.set_df_property('wir_amount', 'read_only', 1);
        if (!refresh) {
            update_wir(frm);
        }
    } else {
        cur_frm.set_df_property('wir_amount', 'read_only', 0);
    }
}

function update_barcodes(frm) {
    frappe.call({
        'method': 'seg.seg.delivery.check_barcodes',
        'args': {
            'doc': frm.doc
        },
        'callback': function(response) {
            if (response.message) {
                let new_barcodes = response.message;
                let removed_barcodes = "";
                for (let i = 0; i < new_barcodes.length; i++) {
                    if (!new_barcodes[i].barcode) {
                        removed_barcodes = removed_barcodes + "<br>" +  new_barcodes[i].item_code;
                    } else {
                        frappe.model.set_value(frm.doc.items[0].doctype, new_barcodes[i].line_name, "barcode", new_barcodes[i].barcode);
                    }
                }
                frappe.show_alert("Barcodes wurden aktualisiert", 3);
                if (removed_barcodes.length > 0) {
                    frappe.msgprint("Folgende Artikel müssen manuell bearbeitet werden, da der Barcode komplett entfernt wurde <br>" + removed_barcodes);
                }
            }
        }
    });
}

function add_pricing_rule(customer=null) {
    let updating_fields = false;
    var d = new frappe.ui.Dialog({
        'title': __('Preisregel erstellen'),
        'fields': [
            {'fieldname': 'customer', 'fieldtype': 'Link', 'label': __('Customer'), 'options': 'Customer', 'reqd': 1, 'default': customer},
            {'fieldname': 'type', 'fieldtype': 'Select', 'label': __('Typ'), 'options': 'Allgemein\nProduktkategorie\nProduktunterkategorie\nProduktgruppe\nArtikelgruppe\nArtikel', 'reqd': 1, 'default': 'Allgemein','onchange': function() { clear_fields() } },
            {'fieldname': 'product_category', 'fieldtype': 'Link', 'label': __('Product Category'), 'options': 'Item Group', 'get_query': get_product_categories(), 'depends_on': 'eval:doc.type=="Produktkategorie"'},
            {'fieldname': 'product_subcategory', 'fieldtype': 'Link', 'label': __('Product Subcategory'), 'options': 'Item Group', 'get_query': get_product_subcategories(), 'depends_on': 'eval:doc.type=="Produktunterkategorie"'},
            {'fieldname': 'product_group', 'fieldtype': 'Link', 'label': __('Product Group'), 'options': 'Item Group', 'get_query': get_product_groups(), 'depends_on': 'eval:doc.type=="Produktgruppe"'},
            {'fieldname': 'item_group', 'fieldtype': 'Link', 'label': __('Item Group'), 'options': 'Item Group', 'get_query': get_item_groups(), 'depends_on': 'eval:doc.type=="Artikelgruppe"'},
            {'fieldname': 'item', 'fieldtype': 'Link', 'label': __('Item'), 'options': 'Item', 'depends_on': 'eval:doc.type=="Artikel"'},
            {'fieldname': 'discount_percent', 'fieldtype': 'Percent', 'label': __('Rabattprozent'), 'reqd': 1},
            {'fieldname': 'selling_price', 'fieldtype': 'Currency', 'label': __('Verkaufspreis'), 'depends_on': 'eval:doc.item'},
            {'fieldname': 'seg_purchase_price', 'fieldtype': 'Currency', 'label': __('SEG EK'), 'read_only': 1, 'depends_on': 'eval:doc.item'},
            {'fieldname': 'price_list_rate', 'fieldtype': 'Currency', 'label': __('Pricelist Rate'), 'read_only': 1, 'depends_on': 'eval:doc.item'},
            {'fieldname': 'db', 'fieldtype': 'Percent', 'label': __('DB'), 'read_only': 1, 'depends_on': 'eval:doc.item'}
        ],
        
        'primary_action': function() {
            d.hide();
            var values = d.get_values();
            frappe.call({
                'method': "seg.seg.report.seg_preisliste.seg_preisliste.create_pricing_rule",
                'args':{
                    'customer': values.customer,
                    'discount_percentage': values.discount_percent,
                    'product_category': values.product_category,
                    'product_subcategory': values.product_subcategory,
                    'product_group': values.product_group,
                    'item_group': values.item_group,
                   'item_code': values.item
                },
                'callback': function(r)
                {
                    //frappe.set_route("Form", "Pricing Rule", r.message)
                    frappe.show_alert( __("Neue Preisregel erstellt: ") + "<a href=\"/desk#Form/Pricing Rule/" +  r.message + "\">" + r.message + "</a>");
                    frappe.query_report.refresh();
                }
            });
        },
        'primary_action_label': __('Erstellen'),
    
    });
    
    //Set Price List Rate, Selling Price and SEG Purchase Price
    d.fields_dict.item.df.onchange = function() {
        set_item_values(d);
    };
    
    //Calculate Discount Percentage/Selling Price and DB
    d.fields_dict.discount_percent.df.onchange = function() {
        recalculate_values(d, "discount_percent");
    };
    
    d.fields_dict.selling_price.df.onchange = function() {
        recalculate_values(d, "selling_price");
    };
    
    d.show();
    
    function clear_fields() {
        d.set_value('product_category', null);
        d.set_value('product_subcategory', null);
        d.set_value('product_group', null);
        d.set_value('item_group', null);
        d.set_value('item', null);
    }
    
    function set_item_values(d) {
        let item_code = d.get_value('item');
        if (item_code) {
            frappe.call({
                'method': 'seg.seg.report.seg_preisliste.seg_preisliste.get_items_prices',
                'args': {
                    'item_code': item_code
                },
                'callback': function(response) {
                    if (response.message) {
                        d.set_value("selling_price", response.message.price_list_rate);
                        d.set_value("price_list_rate", response.message.price_list_rate);
                        d.set_value("seg_purchase_price", response.message.seg_purchase_price);
                    } else {
                        d.set_value("selling_price", null);
                        d.set_value("price_list_rate", null);
                        d.set_value("seg_purchase_price", null);
                    }
                }
            });
        }
    }
    
    function recalculate_values(d, trigger) {
        if (!updating_fields) {
            let price_list_rate = d.get_value('price_list_rate');
            let selling_price = d.get_value('selling_price');
            updating_fields = true
            
            //Calculate Selling Price / Discount Percentage
            if (trigger == "discount_percent") {
                let discount_percentage = d.get_value('discount_percent');
                selling_price = price_list_rate * (1 - discount_percentage / 100);
                d.set_value("selling_price", selling_price).then(() => {
                    updating_fields = false
                });
            }
            
            if (trigger == "selling_price") {
                let discount_percentage = (1 - selling_price / price_list_rate) * 100;
                d.set_value("discount_percent", discount_percentage).then(() => {
                    updating_fields = false
                });
            }
            
            //Calcualte DB
            let seg_purchase_price = d.get_value('seg_purchase_price');
            let db = ((selling_price - seg_purchase_price) / selling_price) * 100;
            d.set_value("db", db)
        }
    }
}

function get_product_categories() {
    return {
        filters: [
            ['item_group_type', "=", "Product Category"]
        ]
    };
}

function get_product_subcategories() {
    return {
        filters: [
            ['item_group_type', "=", "Product Subcategory"]
        ]
    };
}

function get_product_groups() {
    return {
        filters: [
            ['item_group_type', "=", "Product Group"]
        ]
    };
}

function get_item_groups() {
    return {
        filters: [
            ['item_group_type', "=", "Item Group"]
        ]
    };
}

