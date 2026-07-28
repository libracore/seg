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
        console.log(key, label);
		this.key = key;
		this.label = label;
        this.colors = {
                    'purchase_receipt': "#1976d2",
                    'stock_enter': "#43a047"
                }
	}
    
	render() {
		return frappe.render_template(this.key, {});
	}
    
    add_general_event_handlers() {
        //Home Button
        document.getElementById("nav-home").addEventListener("click", () => {
            frappe.stock_management.load_tab(new HomePage());
        });
    }
}

class HomePage extends StockManagementClass {
	constructor() {
		super('home', "Home");
        this.tab_instances = [
            new PurchaseRecieptPage(),
            new StockEnterPage("stock_enter", "Artikel einlagern"),
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
		document.getElementById("goods-receipt").addEventListener("click", () => {
            frappe.stock_management.load_tab(this.tab_instances[0]);
		});
    }
    
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
		this.on_show()
	}

	on_show() {
        this.show_subsections();
        //~ this.show_dynamic_content();
	}
    
    show_subsections() {
        console.log("show_subsections");
        //Show Navbar
        const header_menu_section = document.getElementById('stock-enter-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Item Input
        //~ const item_input = document.getElementById('stock-enter-input');
        //~ const item_input_content = frappe.render_template("item_input", {'title': this.label});
        //~ item_input.innerHTML = item_input_content;
        
        //~ //Show Item Table
        //~ console.log(this.items);
        //~ const list_section = document.getElementById('stock-enter-list');
        //~ const list_section_content = frappe.render_template("stock_enter_list", {'items': this.items});
        //~ list_section.innerHTML = list_section_content;
        
        //~ //Show Bottom Button
        //~ const bottom_button = document.getElementById('stock-enter-button');
        //~ const bottom_button_content = frappe.render_template("bottom_button", {'items': this.items});
        //~ bottom_button.innerHTML = bottom_button_content;
        
    }
}

class StockEnterPage extends StockManagementClass {
	constructor(key, label) {
        console.log(key, label);
		super(key, label);
        this.items;
	}

	init() {
        this.get_entry_warehouse_items();
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Home <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(new HomePage());
		});
        
        //Close Stock Entry and Go to Home
		document.getElementById("action-button").addEventListener("click", () => {
            frappe.stock_management.load_tab(new HomePage());
		});
        
        document.getElementById("clear-article").addEventListener("click", () => {
            const articleInput = document.getElementById("article-input");

            articleInput.value = "";
            articleInput.focus();
        });
        
        document.getElementById("qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });

        document.getElementById("qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Open Item Tab
		document.getElementById("ok-button").addEventListener("click", () => {
            let item = document.getElementById("article-input").value;
            frappe.stock_management.load_tab(new StockEnterItem(item));
		});
    }
    
    show_subsections() {
        console.log("show_subsections");
        //Show Navbar
        const header_menu_section = document.getElementById('stock-enter-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Item Input
        const item_input = document.getElementById('stock-enter-input');
        const item_input_content = frappe.render_template("item_input", {'title': this.label});
        item_input.innerHTML = item_input_content;
        
        //Show Item Table
        console.log(this.items);
        const list_section = document.getElementById('stock-enter-list');
        const list_section_content = frappe.render_template("stock_enter_list", {'items': this.items});
        list_section.innerHTML = list_section_content;
        
        //Show Bottom Button
        const bottom_button = document.getElementById('stock-enter-button');
        const bottom_button_content = frappe.render_template("bottom_button", {'items': this.items});
        bottom_button.innerHTML = bottom_button_content;
        
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
    
    show_specific_dynamic_content() {
        document.getElementById("action-button").textContent = "Einlagerung abschliessen";
        document.getElementById("action-button").style.backgroundColor = this.colors.stock_enter;
        document.getElementById("ok-button").style.backgroundColor = this.colors.stock_enter;
        this.show_dynamic_content()
    }
    
    show_dynamic_content() {
        document.getElementById("nav-title").textContent = this.label;
        document.getElementById("nav-back").style.backgroundColor = this.colors.stock_enter;
        document.getElementById("mobile-navbar").style.backgroundColor = this.colors.stock_enter;
    }
}
//~ class StockEnterList extends StockEnterPage {
	//~ constructor() {
		//~ super('stock_enter_list', "Stock Enter List");
	//~ }
    
	//~ on_show() {
        //~ this.show_dynamic_text();
	//~ }
    
    //~ show_dynamic_text() {
        //~ document.getElementById("dummy-button")
    //~ }
//~ }

class StockEnterItem extends StockEnterPage {
	constructor(item) {
        console.log(item);
		super('stock_enter_item', "Zielplatz");
        this.item = item;
        this.items;
	}

	init() {
        this.get_item_information(this.item);
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Stock Enter Page <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(this.tab_instances[1]);
		});
        
        document.getElementById("clear-warehouse").addEventListener("click", () => {
            const warehouseInput = document.getElementById("warehouse-input");

            warehouseInput.value = "";
            warehouseInput.focus();
        });
        
        document.getElementById("wh-qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });

        document.getElementById("wh-qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
    }
    
    show_subsections() {
        console.log("show_subsections_item");
        console.log(this.item);
        console.log(this.items);
        //Show Navbar
        const header_menu_section = document.getElementById('stock-enter-item-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Item Input
        const item_input = document.getElementById('stock-enter-item-input');
        const item_input_content = frappe.render_template("warehouse_input", {'title': this.label});
        item_input.innerHTML = item_input_content;
        
        //Show Single Item Table
        const list_section = document.getElementById('stock-enter-item-list');
        const list_section_content = frappe.render_template("stock_enter_item_list", {'items': this.items});
        list_section.innerHTML = list_section_content;
        
        //~ //Show Bottom Button
        //~ const bottom_button = document.getElementById('stock-enter-button');
        //~ const bottom_button_content = frappe.render_template("bottom_button", {'items': this.items});
        //~ bottom_button.innerHTML = bottom_button_content;
        
		//~ document.getElementById("dummy-button").addEventListener("click", () => {
            //~ this.update_stocked_amount("201835-B1", 2);
		//~ });
        
    }
    
    //~ update_stocked_amount(item_code, new_amount) {
        //~ const target_item = this.items.find(item => item.item_code === item_code);
        //~ target_item.content['stored_qty'] = target_item.content['stored_qty'] + new_amount;
        //~ this.refresh_stocked_amount(item_code, target_item.content['qty'], target_item.content['stored_qty']);
    //~ }
    
    //~ refresh_stocked_amount(item_code, qty, new_amount) {
        //~ const progress_div = document.getElementById(item_code + "_amount");
        //~ progress_div.innerText = new_amount + "/" + qty;
    //~ }
    
    show_specific_dynamic_content() {
        //~ document.getElementById("nav-title").textContent = "Zielplatz";
        document.getElementById("wh-ok-button").style.backgroundColor = this.colors.stock_enter;
        this.show_dynamic_content()
    }
    
    get_item_information(item) {
        if (item) {
            frappe.call({
                'method': 'seg.seg.page.stock_management.stock_management.get_single_item_information',
                'args': {
                    'item': this.item
                },
                'callback': (response) => {
                    this.items = response.message;
                    this.on_show();
                }
            });
        } else {
            return false
        }
    }
}
