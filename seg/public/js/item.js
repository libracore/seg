// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item',  {
    refresh: function(frm) {
        if (!cur_frm.doc.__islocal) {
            frm.add_custom_button(__("French Attributes"),  function(){
              set_french_attributes(frm);
            });
            
            add_nextcloud_button(frm);
            set_description_properties(frm);
        }
    },
    before_save: function(frm) {
        //Set default supplier (first from supplier_items List)
        set_default_supplier(frm);
        //Remove existing default Variant if a new has been set or item has been disabled
        check_default_variant(frm);
        //Remove show in Website if item is disabled
        if (frm.doc.disabled) {
            cur_frm.set_value("show_in_website", 0);
            cur_frm.set_value("show_variant_in_website", 0);
        }
    },
    packaging_type: function(frm) {
        set_french_packaging_type(frm);
    }
});

frappe.ui.form.on('Item Reorder',  {
    reorder_levels_add: function(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "warehouse_reorder_qty", frm.doc.order_recommendation_supplier);
    }
});

function set_french_attributes(frm) {
    frappe.call({
        'method': 'seg.seg.utils.set_french_attributes',
        'args': {
            'self': frm.doc.name,
            'event': "button"
        },
        'callback': function(response) {
            show_alert('Französische Attribute wurden gesetzt!', 3);
            cur_frm.reload_doc();
        }
    });
}

function set_french_packaging_type(frm) {
    if (frm.doc.packaging_type == "Karton") {
        cur_frm.set_value("packaging_type_fr", "Carton");
    } else if (frm.doc.packaging_type == "Palette") {
        cur_frm.set_value("packaging_type_fr", "Palette");
    }
}

//Old code, maybe to be used again
//~ function set_main_attribute_options(frm) {
    //~ if (frm.doc.attributes && frm.doc.attributes) {
        //~ var options = [];
        //~ for (i=0; i < frm.doc.attributes.length; i++) {
            //~ if (frm.doc.attributes[i].attribute) {
                //~ options.push(frm.doc.attributes[i].attribute);
            //~ }
        //~ }
        //~ var options_string = options.join("\n");
        //~ frm.set_df_property('main_variant_attribute', 'options', options_string);
        //~ frm.set_df_property('main_variant_attribute', 'hidden', false);
    //~ }
//~ }

function set_default_supplier(frm) {
    var default_supplier = false
    if (frm.doc.supplier_items && frm.doc.supplier_items.length > 0) {
        default_supplier = frm.doc.supplier_items[0].supplier;
    }
    
    if (default_supplier && default_supplier != frm.doc.default_supplier) {
        cur_frm.set_value("default_supplier", default_supplier);
    } else if (frm.doc.default_supplier && !default_supplier) {
        cur_frm.set_value("default_supplier", null);
    }
}

function set_description_properties(frm) {
    if (frm.doc.variant_of) {
         cur_frm.set_df_property('web_long_description', 'read_only', 1);
         cur_frm.set_df_property('website_description_fr', 'read_only', 1);
    }
}

function check_default_variant(frm) {
    if (frm.doc.default_variant) {
        if (frm.doc.disabled) {
            cur_frm.set_value("default_variant", 0);
        } else {
            frappe.call({
                'method': 'seg.seg.utils.unset_default_variants',
                'args': {
                    'item_code': frm.doc.name,
                    'template': frm.doc.variant_of
                },
                'callback': function(response) {
                    if (response.message) {
                        frappe.show_alert("Die bisherige Standardvariante wurde entfernt.", 5);
                    }
                }
            });
        }
    }
}
