// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quotation',  {
    refresh: function(frm) {
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
        
        //Check if Customer always picks up
        if (cur_frm.doc.__islocal) {
            cur_frm.set_value("taxes_and_charges", "MwSt, LSVA und VOC 2024 - SEG");
            if (frm.doc.quotation_to == "Customer" && frm.doc.party_name) {
                check_pick_up(frm.doc.party_name);
            } else {
                cur_frm.set_value("picked_up" , 0);
            }
        }
    },
    party_name: function(frm) {
        if (frm.doc.quotation_to == "Customer" && frm.doc.party_name) {
            check_pick_up(frm.doc.party_name);
        } else {
            cur_frm.set_value("picked_up" , 0);
        }
    },
	before_save: function(frm) {
        // update VOC
        update_voc(frm);
        if (frm.doc.picked_up == 1) {
            frm.doc.taxes.forEach(function(entry) {
               if (entry.account_head == "2209 Geschuldete LSVA - SEG") {
                   console.log(entry.name);
                   frappe.model.set_value("Sales Taxes and Charges", entry.name, 'tax_amount', 0);
               } 
            });
        } else {
            // get total weight, update weight and LSVA
            getTotalWeight();
        }
    }
});
