// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

// Prepared for later Task, not added to Hooks yet
frappe.listview_settings['Sales Order'] = {
    refresh: function(me) {
        $(".list-row-container").each(function(i,onj){
            let data = $(this).data('data');
            console.log(data);
            $(this).css('background-color', '#F3FADC');
        })
    }
};

//~ frappe.listview_settings['Sales Order'] = {
    //~ listview.on('render_complete', () => {
        //~ listview.$result.find(".list-row").each(function() {
            //~ const data = $(this).data("data");
            //~ if (data && data.status === "Overdue") {
                //~ $(this).find(".list-subject a").css("color", "red");
            //~ }
        //~ });
    //~ });
//~ }
