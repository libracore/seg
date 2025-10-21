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
        toggle_wir_amount(frm);
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
	before_save: function(frm) {
        // update VOC
        update_voc(frm);
        if (frm.doc.picked_up == 1) {
            frm.doc.taxes.forEach(function(entry) {
               if (entry.account_head == "2209 Geschuldete LSVA - SEG") {
                   frappe.model.set_value("Sales Taxes and Charges", entry.name, 'tax_amount', 0);
               } 
            });
        } else {
            // get total weight, update weight and LSVA
            getTotalWeight();
        }
    },
    wir_percent: function(frm) {
        update_wir(frm);
    },
    validate: function(frm) {
        update_wir(frm);
    },
    set_manual_wir_amount: function(frm) {
        toggle_wir_amount(frm);
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

function toggle_wir_amount(frm) {
   if (!frm.doc.set_manual_wir_amount) {
       cur_frm.set_df_property('wir_amount', 'read_only', 1);
       update_wir(frm);
   } else {
       cur_frm.set_df_property('wir_amount', 'read_only', 0);
   }
}
