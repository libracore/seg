// Copyright (c) 2026, libracore AG and contributors
// For license information, please see license.txt

frappe.pages['stock-management'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Stock Management',
		single_column: true
	});
    
    frappe.stock_management.add_views(page);
}

frappe.pages['stock-management'].on_page_show = function(wrapper) {
	frappe.stock_management.show_view('stock_management');

	// load home by default
	frappe.stock_management.load_tab(new HomePage());
}


frappe.stock_management = {
	add_views: function(page) {
		page.add_view('stock_management', frappe.render_template("stock_management", {}));
	},
    
	load_tab: function(tab_instance) {
		//render new tab content
		const tab_content = tab_instance.render();
		const content_el = document.getElementById("stock-management-content");
		content_el.innerHTML = tab_content;

		tab_instance.init();
		this.current_tab = tab_instance;
	},

	show_view: function(view_name) {
		cur_page.page.page.set_view(view_name);
	}

}

class StockManagementClass {
	constructor(key, label) {
		this.key = key;
		this.label = label;
	}
    
	render() {
		return frappe.render_template(this.key, {});
	}
    
    
}

class HomePage extends StockManagementClass {
	constructor() {
		super('home', "Home");
        this.tab_instances = [
            new PurchaseRecieptPage(),
            new StockEnterPage(),
            //~ new TransferPage(),
            //~ new PickingPage(),
            //~ new CreateOrderPage()
        ];
	}
    
    //Called when Page is initialized
	init() {
		this.add_event_listeners()
	}
    
    //Called when Page is Shown
	on_show() {
        
	}
    
    //Add Event Listeners
    add_event_listeners() {
		document.getElementById("stock-enter-icon").addEventListener("click", () => {
            frappe.stock_management.load_tab(this.tab_instances[1]);
		});
    }
}

class PurchaseRecieptPage extends StockManagementClass {
	constructor() {
		super('purchase_receipt', "Wareneingang");
	}

	init() {
		
	}

	on_show() {
    
	}
}

class StockEnterPage extends StockManagementClass {
	constructor() {
		super('stock_enter', "Einlagern");
        this.items;
	}

	init() {
        this.get_entry_warehouse_items();
        this.add_event_listeners();
	}

	on_show() {
        this.show_subsections();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        
    }
    
    show_subsections() {
        //Show Item Table
        const list_section = document.getElementById('stock-enter-list');
        const list_section_content = frappe.render_template("stock_enter_list", {'items': this.items});
        list_section.innerHTML = list_section_content;
        
        //Show Navbar
        const header_menu_section = document.getElementById('stock-enter-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
		document.getElementById("dummy-button").addEventListener("click", () => {
            this.update_stocked_amount("201835-B1", 2);
		});
        
    }
    
    get_entry_warehouse_items() {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.get_entry_warehouse_items',
            'args': {
                //No args yet
            },
            'callback': (response) => {
                this.items = response.message;
                this.on_show();
            }
        });
    }
    
    update_stocked_amount(item_code, new_amount) {
        const target_item = this.items.find(item => item.item_code === item_code);
        target_item.content['stored_qty'] = target_item.content['stored_qty'] + new_amount;
        this.refresh_stocked_amount(item_code, target_item.content['qty'], target_item.content['stored_qty']);
    }
    
    refresh_stocked_amount(item_code, qty, new_amount) {
        const progress_div = document.getElementById(item_code + "_amount");
        progress_div.innerText = new_amount + "/" + qty;
    }
}
