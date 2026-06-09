// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quotation',  {
    refresh: function(frm) {
        // custom mail dialog
        cur_frm.page.add_action_icon("es-line-email", function() {
            custom_mail_dialog(frm);
        }, "", "Email");
        let target = $('span.menu-item-label').filter(function() {
            return $(this).text().trim() === __('Email');
        });
        $(target).parent().parent().remove();   // remove Menu > Email
        
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
                   frappe.model.set_value("Sales Taxes and Charges", entry.name, 'tax_amount', 0);
               } 
            });
        } else {
            // get total weight, update weight and LSVA
            getTotalWeight();
        }
    }
});
