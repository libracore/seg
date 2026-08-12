frappe.ui.form.on('Sales Order',  {
    refresh: function(frm) {
        if (frm.doc.customer) {
            check_cash_discount(frm);
        }
        
        //Set picked up if customer is marked as "always picks up"
        if (cur_frm.doc.__islocal) {
            if (frm.doc.customer) {
                check_pick_up(frm.doc.customer);
                set_fixed_wir_percentage(frm);
            } else {
                cur_frm.set_value("picked_up" , 0)
            }
            //Set Document Owner for List View
            set_doc_owner();
        }
        
        if ((frm.doc.sales_team) && (frm.doc.sales_team.length === 0) && (frm.doc.customer)) {
            // fetch sales team from customer
            frappe.call({
                "method": "frappe.client.get",
                "args": {
                    "doctype": "Customer",
                    "name": frm.doc.customer
                },
                "callback": function(response) {
                    var customer = response.message;
                    if (customer.sales_team) {
                        for (var i = 0; i < customer.sales_team.length; i++) {
                            var child = cur_frm.add_child('sales_team');
                            frappe.model.set_value(child.doctype, child.name, 'sales_person', customer.sales_team[i].sales_person);
                            frappe.model.set_value(child.doctype, child.name, 'allocated_percentage', customer.sales_team[i].allocated_percentage);
                        }
                        cur_frm.refresh_field('sales_team');
                    } 
                }
            });
        }
        toggle_wir_amount(frm, true);
        
        //Filter Transporter Field
		frm.set_query('transporter', function() {
			return {
				filters: {
					'is_transporter': 1
				}
			}
		});
        
        // custom mail dialog
        cur_frm.page.add_action_icon("es-line-email", function() {
            custom_mail_dialog(frm);
        }, "", "Email");
        let target = $('span.menu-item-label').filter(function() {
            return $(this).text().trim() === __('Email');
        });
        $(target).parent().parent().remove();   // remove Menu > Email
        
        if (!frm.doc.ignore_pricing_rule) {
            frm.add_custom_button(__("Detach From Pricing Rule"), function() {
                modify_item_rate(frm);
            });
        }
        
        //Add Button to create Picking List
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__("Picking List"), () => create_picking_list(frm), __("Create"));
        }
    },
    delivery_date: function(frm) {
        frm.doc.desired_date = frm.doc.delivery_date;
    },
    customer: function(frm) {
        //Set picked up if customer is marked as "always picks up"
        if (frm.doc.customer) {
            check_pick_up(frm.doc.customer);
        } else {
            cur_frm.set_value("picked_up" , 0)
        }
        set_fixed_wir_percentage(frm);
    },
	validate: function(frm) {
        if (frm.doc.only_samples == 1) {
            var taxes = cur_frm.doc.taxes;
            if (taxes.length > 0) {
                taxes.forEach(function(entry) {
                    /* enter VOC target account here */
                    if (entry.account_head.startsWith("2208 ")) {
                        frappe.model.set_value("Sales Taxes and Charges", 
                        entry.name, 'tax_amount', 0);
                    } 
                });
            }
        } else {
            // update VOC
            update_voc(frm);
        }
        
        //Set Rates for Sample Sales Order
        
        if (frm.doc.picked_up == 1 || frm.doc.only_samples == 1) {
            frm.doc.taxes.forEach(function(entry) {
               if (entry.account_head == "2209 Geschuldete LSVA - SEG") {
                   frappe.model.set_value("Sales Taxes and Charges", entry.name, 'tax_amount', 0);
               } 
            });
        } else {
            // get total weight, update weight and LSVA
            getTotalWeight();
        }
        update_wir(frm);
    },
    wir_percent: function(frm) {
        update_wir(frm);
    },
    set_manual_wir_amount: function(frm) {
        toggle_wir_amount(frm);
    },
    only_samples: function(frm) {
        if (!frm.doc.only_samples) {
            cur_frm.set_value("ignore_pricing_rule", 0);
        }
        set_sample_rates(frm);
    },
    discount_percentage: function(frm) {
        console.log("ok");
    }
});

function check_cash_discount(frm) {
    frappe.call({
        'method': "seg.seg.utils.check_cash_discount",
        'args': {
            'customer': frm.doc.customer
        },
        'callback': function(response) {
            var cash_discount = response.message;
            if (cash_discount) {
                cur_frm.dashboard.add_comment( "Achtung, Kunde " + cur_frm.doc.customer_name + " hat " + cash_discount + "% Skonto hinterlegt.", 'yellow', true);
            }
        }
    });
}

function set_sample_rates(frm) {
    if (cur_frm.doc.only_samples) {
        cur_frm.set_value("ignore_pricing_rule", 1).then(() => {
            for (let i = 0; i < frm.doc.items.length; i++) {
                if (!frm.doc.items[i].original_rate_set) {
                    frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate", frm.doc.items[i].rate).then(() => {
                        frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate_set", 1).then(() => {
                            frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "discount_percentage", 100).then(() => {
                                cur_frm.refresh_field('items');
                            })
                        })
                    });
                }
            }
        });
    } else {
        for (let i = 0; i < frm.doc.items.length; i++) {
            if (frm.doc.items[i].original_rate_set) {
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "rate", frm.doc.items[i].original_rate);
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate_set", 0);
                frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, "original_rate", 0);
            }
        }
    }
    
}

function set_doc_owner() {
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "User",
            name: frappe.session.user
        },
        callback: function(response) {
            if (response.message) {
                let first_name = response.message.first_name;
                cur_frm.set_value("doc_owner", first_name);
            }
        }
    });
}

function create_picking_list(frm) {
    frappe.call({
        'method': 'seg.seg.delivery.create_pircking_list',
        'args': {
            'doc': frm.doc
        },
        'callback': function(response) {
            if (response.message.success) {
                frappe.set_route("Form", "Picking List", response.message.name);
            } else {
                frappe.msgprint("Es ist ein Fehler beim erstellen der Picking List aufgetreten, ein Fehlerbericht wurde erstellt.")
            }
        }
    });
}

