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
		tab_instance.on_show();
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
        console.log("I am rednering");
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
            console.log("Hallo Velo");
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
        this.get_entry_warehouse_items()
        this.add_event_listeners()
	}

	on_show() {
        this.show_subsections();
	}
    
    //Add Event Listeners
    add_event_listeners() {
		//~ document.getElementById("stock-enter-icon").addEventListener("click", () => {
            //~ console.log("Hallo Velo");
            //~ frappe.stock_management.load_tab(this.tab_instances[1]);
		//~ });
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
    }
    
    get_entry_warehouse_items() {
        this.items = [{'picture': "PIC1", 'content': {'qty': 12, 'item_name': "Scheidemesser"}}, {'picture': "PIC2", 'content': {'qty': 24, 'item_name': "Cutter"}}]
    }
}
