frappe.ui.form.on('Sales Invoice',  {
    customer: function(frm) {
        if (frm.doc.customer) {
            check_customer_mahnsperre(frm);
        } else {
            cur_frm.set_value("mahnsperre", 0);
        }
        check_email_invoice(frm);
    },
    before_save: function(frm) {
        update_discout(frm)
        if ((frm.doc.is_return === 1) && (frm.doc.wir_amount > 0)) {
            update_wir_for_sinv_return(frm);
        }
        
        if ((frm.doc.mahnsperre === 1) && (frm.doc.is_return === 0)) {
            cur_frm.set_value("exclude_from_payment_reminder_until", "2099-12-31");
        } else if (frm.doc.is_return === 0) {
            // do not remind 20 days
            cur_frm.set_value("exclude_from_payment_reminder_until",frappe.datetime.add_days(frm.doc.due_date, 20));
        }
    },
    refresh: function(frm) {
        if (frm.doc.__islocal) {
            set_naming_series(frm);
        }
        if (frm.doc.customer) {
            check_cash_discount(frm);
        }
        if (frm.doc.docstatus == 1) {
            // custom mail dialog (prevent duplicate icons on creation)
            if (document.getElementsByClassName("fa-envelope-o").length === 0) {
                cur_frm.page.add_action_icon(__("fa fa-envelope-o"), function() {
                    custom_mail_dialog(frm);
                });
                var target ="span[data-label='" + __("Email") + "']";
                $(target).parent().parent().remove();   // remove Menu > Email
            }
        }
        check_email_invoice(frm);
    },
    is_return: function(frm) {
        if (frm.doc.__islocal) {
            set_naming_series(frm);
        }
    }
});

function check_customer_mahnsperre(frm) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Customer",
            'name': frm.doc.customer
        },
        "callback": function(response) {
            var mahnsperre = response.message.mahnsperre;
            if (mahnsperre === 1) {
                cur_frm.set_value("mahnsperre", 1);
            } else {
                cur_frm.set_value("mahnsperre", 0);
            }
        }
    });
}

function update_wir_for_sinv_return(frm) {
    var return_wir_amount = 0;
    frm.doc.items.forEach(function(item) {
        return_wir_amount += item.wir_amount_on_item;
    });
    cur_frm.set_value("wir_amount", return_wir_amount);
}

function update_discout(frm) {
    // check if there is a discount from delivery notes
    var dn_discount_total= 0;
    var current_dn = null;
    
    if (frm.doc.items) {  
        frm.doc.items.forEach(function(item) {
            if (current_dn != item.delivery_note) {
                current_dn = item.delivery_note;
                //console.log("item", item.delivery_note, item.dn_discount_amount)
                dn_discount_total = dn_discount_total + item.dn_discount_amount;
            }
        });
    }
    
    // if there is a discount from delivery notes, set this as an absolute discount
    if (dn_discount_total > 0) {
        cur_frm.set_value("additional_discount_percentage", 0);
        cur_frm.set_value("discount_amount", dn_discount_total);
    }
}

function set_naming_series(frm) {
    if (cur_frm.doc.is_return === 0) {
        cur_frm.set_value("naming_series", "RG-.#####.");
    } else {
        cur_frm.set_value("naming_series", "GS-.#####.");
    }
}

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

function check_email_invoice(frm) {
    if (frm.doc.customer) {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Customer",
                'name': frm.doc.customer
            },
            'callback': function(response) {
                if (response.message) {
                    if (response.message.email_invoices) {
                        cur_frm.dashboard.add_comment( "Kunde hat Emailrechnungsversand!<br>" + response.message.preferred_invoice_email, 'red', true);
                    }
                }
            }
        });
    }
}
