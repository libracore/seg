// Copyright (c) 2026, libracore AG and contributors
// For license information, please see license.txt

frappe.pages['stock-management'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Stock Management',
		single_column: true
	});
    
    frappe.stock_management.add_views(page);
    frappe.stock_management.init_tabs()
}

frappe.pages['stock-management'].on_page_show = function(wrapper) {
	frappe.stock_management.show_view('stock_management');

	// load home by default
	frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
}


frappe.stock_management = {
    tab_instances: {},
    
    init_tabs: function() {
        this.tab_instances.home = new HomePage()
        this.tab_instances.purchase_receipt = new PurchaseReceiptPage("purchase_receipt", "Wareneingang");
        this.tab_instances.stock_enter = new StockEnterPage("stock_enter", "Artikel einlagern");
        this.tab_instances.stock_transfer = new StockTransferPage("stock_transfer", "Artikel umlagern");
        this.tab_instances.picking = new PickingPage("picking", "Artikel Kommissionieren");
        this.tab_instances.create_sales_order = new CreateSalesOrderPage("create_sales_order", "Auftrag erstellen");
    },
    
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
                    'purchase_receipt_sec': "#64B5F6",
                    'stock_enter': "#43a047",
                    'stock_transfer': "#fb8c00",
                    'picking': "#7B4DFF",
                    'crete_sales_order': "#E53935"
                }
	}
    
	render() {
		return frappe.render_template(this.key, {});
	}
    
    add_general_event_handlers() {
        //Home Button
        document.getElementById("nav-home").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
        });
        
        //Control scanned values
        this.setup_scanner()
        
    }
    
    //Display Sucess message
    show_success(message, element) {
        console.log(element);
        const msg = document.getElementById(element);
        msg.textContent = message;
        msg.className = "scan-message success";
        
        setTimeout(() => {
            this.hide_message(element);
        }, 3000);
    }
    
    //Display Error message
    show_error(message, element) {
        const msg = document.getElementById(element);
        msg.textContent = message;
        msg.className = "scan-message error";
        
        setTimeout(() => {
            this.hide_message(element);
        }, 3000);
    }
    
    //Hide Success or Error Message
    hide_message(element) {
        const msg = document.getElementById(element);
        msg.textContent = "";
        msg.className = "scan-message";
    }
    
    //Translate Barcode to Item Code
    translate_item_barcode(barcode) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'seg.seg.page.stock_management.stock_management.get_item_code',
                args: {
                    barcode: barcode
                },
                callback: function(response) {
                    console.log(response.message);
                    resolve(response.message);
                }
            });

        });
    }
    
    get_warehouse_overview(item) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'seg.seg.page.stock_management.stock_management.get_warehouse_overview',
                args: {
                    'item': item
                },
                callback: function(response) {
                    console.log("Warehouses response: " + response.message)
                    resolve(response.message);
                }
            });

        });
    }
    
    //Provide Scan Inputs
    setup_scanner() {
        var me = this;
        let scan_buffer = "";

        document.addEventListener("keydown", (event) => {

            if (event.key === "Enter") {
                me.handle_scan(scan_buffer);
                scan_buffer = "";
                return;
            }

            if (event.key === "Shift") {
                return;
            }

            scan_buffer += event.key;
        });
    }
    
    create_item_dict(item) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'seg.seg.page.stock_management.stock_management.get_single_item_basic_information',
                args: {
                    'item': item
                },
                callback: function(response) {
                    resolve(response.message);
                }
            });

        });
    }
    
    create_item_dict_by_warehouse(warehouse) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'seg.seg.page.stock_management.stock_management.get_item_information_by_warehouse',
                args: {
                    'warehouse': warehouse
                },
                callback: function(response) {
                    resolve(response.message);
                }
            });

        });
    }
    
    create_stock_entry(items, entry_type, element) {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.create_stock_entry',
            'args': {
                'items': items,
                'entry_type': entry_type
            },
            'callback': (response) => {
                if (response.message) {
                    if (response.message.success) {
                        this.show_success("Artikel wurde erfolgreich umgelagert.", element);
                    } else {
                        this.show_error(response.message.error, element);
                    }
                } else {
                    this.show_error("Beim einlagern ist ein Fehler aufgetreten.", element);
                }
            }
        });
    }
}

class HomePage extends StockManagementClass {
	constructor() {
		super('home', "Home");
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
        //Open Receipt
		document.getElementById("goods-receipt").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.purchase_receipt);
		});
        
        //Open Stock Enter
		document.getElementById("stock-enter-icon").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.stock_enter);
		});
        
        //Open Stock Transfer
		document.getElementById("stock-transfer").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.stock_transfer);
		});
        
        //Open Picking
		document.getElementById("picking").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.picking);
		});
        
        //Open Sales Order Creation
		document.getElementById("sales-order").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.create_sales_order);
		});
    }
}

//Purchase Receipt - Pick Order
class PurchaseReceiptPage extends StockManagementClass {
	constructor(key, label) {
		super(key, label);
        this.orders;
        this.selected_supplier;
	}

	init() {
		this.get_open_orders()
	}

	on_show() {
        this.show_subsections();
        this.add_event_listeners();
        this.create_link_fields();
        this.show_specific_dynamic_content();
	}
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('purchase-receipt-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Purchase Order Order Input
        const pruchase_order_input = document.getElementById('purchase-receipt-input');
        const pruchase_order_content = frappe.render_template("purchase_order_input", {'title': this.label});
        pruchase_order_input.innerHTML = pruchase_order_content;
        
        //Show Purchase Order Table
        this.display_orders()
    }
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Home <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
		});
        
        //Delete PO Field
        document.getElementById("clear-purchase-order").addEventListener("click", () => {
            this.purchase_order_link_field.set_value("");
            this.purchase_order_link_field.set_focus();
        });
        
        //Delete Supplier Field
        document.getElementById("clear-supplier").addEventListener("click", () => {
        
            this.supplier_link_field.set_value("");
            this.supplier_link_field.set_focus();

        });
        
        //Open Pruchase Order Tab
		document.getElementById("purchase-order-ok-button").addEventListener("click", () => {
            let order = this.purchase_order_link_field.get_value()
            if (order) {
                frappe.stock_management.load_tab(new PurchaseReceiptOrder('purchase_receipt_order', "Wareneingang", order, this));
            } else {
                this.show_error("Bitte Bestellung angeben.", "purchase-order-input-message");
            }
		});
        
        //Fill PO Field with List PO
        this.set_row_handler()
    }
    
    //Show Dynamic Content specific for this Site
    show_specific_dynamic_content() {
        document.getElementById("nav-title").textContent = this.label;
        document.getElementById("purchase-order-ok-button").style.backgroundColor = this.colors.purchase_receipt;
        this.show_dynamic_content()
    }
    
    //Show Dynmic Content for whole Purchase Receipt Classes
    show_dynamic_content() {
        document.getElementById("nav-back").style.backgroundColor = this.colors.purchase_receipt;
        document.getElementById("mobile-navbar").style.backgroundColor = this.colors.purchase_receipt;
    }
    
    get_open_orders(refresh=false) {
        const supplier = this.selected_supplier ?? "";
        const order = document.getElementById("purchase-order-input")?.value ?? "";
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.get_open_orders',
            'args': {
                'supplier': supplier,
                'order': order
            },
            'callback': (response) => {
                this.orders = response.message;
                if (!refresh) {
                    this.on_show();
                } else {
                    this.refresh_order_list()
                }
            }
        });
    }
    
    create_link_fields() {
        //Pruchase Order
        const order_container = document.getElementById("purchase-order-input");

        this.purchase_order_link_field = frappe.ui.form.make_control({
            parent: order_container,
            df: {
                fieldtype: "Link",
                options: "Purchase Order",
                fieldname: "purchase_order",
                get_query: () => {
                    const filters = {
                        'docstatus': 1,
                        'per_received': ["<", 100],
                        'status': ["!=", "Closed"]
                    }
                    
                    if (this.selected_supplier) {
                        filters.supplier = this.selected_supplier
                    }
                    
                    return {
                        filters: filters
                    };
                },
				change: () => {
                    document.activeElement.blur();
				}
            },
            only_input: true
        });

        this.purchase_order_link_field.make();
        this.purchase_order_link_field.refresh();
        
        //Supplier
		const container = document.getElementById("supplier-input");

		this.supplier_link_field = frappe.ui.form.make_control({
			parent: container,
			df: {
				fieldtype: "Link",
				options: "Supplier",
				name: "supplier",
				change: () => {
					this.selected_supplier = this.supplier_link_field.get_value();
                    document.activeElement.blur();
                    this.get_open_orders(true)
				}
			},
			only_input: true
		});
        this.supplier_link_field.make()
		this.supplier_link_field.refresh();
    }
    
    refresh_order_list() {
        this.display_orders()
    }
    
    display_orders() {
        const list_section = document.getElementById('purchase-receipt-list');
        const list_section_content = frappe.render_template("purchase_receipt_list", {'orders': this.orders});
        list_section.innerHTML = list_section_content;
        this.set_row_handler()
    }
    
    set_row_handler() {
        document.querySelectorAll(".order-row").forEach(row => {
            row.addEventListener("click", () => {
                const order = row.dataset.order;
                const target_item = this.orders.find(item => item.name === order);
                this.purchase_order_link_field.set_value(target_item.name)
            });
		});
    }
}

//Purchase Receipt - Show Orders with Items to Receive - Pick Items
class PurchaseReceiptOrder extends PurchaseReceiptPage {
	constructor(key, label, order, parent_this) {
		super(key, label);
        this.order = order;
        this.parent_this = parent_this;
        this.items;
	}

	init() {
        this.get_order_items();
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Stock Enter Page <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.purchase_receipt);
		});
        
        //Cleare Item
        document.getElementById("clear-article").addEventListener("click", () => {
            this.item_link_field.set_value("");
            this.item_link_field.set_focus();
        });
        
        //Add Quantity
        document.getElementById("qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //remove Quantity
        document.getElementById("qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Submit Stock Entry
		document.getElementById("action-button").addEventListener("click", () => {
            this.store_everything(this.order, true);
		});
        
        //Create Stock Entry
		document.getElementById("secondary-action-button").addEventListener("click", () => {
            this.store_everything(this.order, false);
		});
        
        //Open Item Tab
		document.getElementById("ok-button").addEventListener("click", () => {
            if (this.item) {
                const target_item = this.items.find(item => item.item_code === this.item);
                if (target_item) {
                    let qty = document.getElementById("quantity-input").value;
                    frappe.stock_management.load_tab(new PurchaseReceiptItem(this.item, qty, this, this.parent_this));
                } else {
                    this.show_error("Kein Artikel in dieser Bestellung gefunden.", "item-input-message");
                }
            } else {
                this.show_error("Bitte zuerst den Artikel angeben.", "item-input-message");
            }
		});
        
        //Fill Item Field with List Item
        document.querySelectorAll(".item-row").forEach(row => {
            row.addEventListener("click", () => {
                const item_code = row.dataset.item;
                const target_item = this.items.find(item => item.item_code === item_code);
                this.item_link_field.set_value(item_code);
                document.getElementById("quantity-input").value = target_item.content.qty;
            });
		});
    }
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('purchase-receipt-order-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Item Input
        const item_input = document.getElementById('purchase-receipt-order-input');
        const item_input_content = frappe.render_template("item_input", {'title': this.label});
        item_input.innerHTML = item_input_content;
        
        //Show Item Table
        const list_section = document.getElementById('purchase-receipt-order-list');
        const list_section_content = frappe.render_template("items_list_without_counter", {'items': this.items});
        list_section.innerHTML = list_section_content;
        
        //Show Bottom Button
        const bottom_button = document.getElementById('purchase-receipt-order-button');
        const bottom_button_content = frappe.render_template("bottom_button");
        bottom_button.innerHTML = bottom_button_content;
        
        //Show Secundary Bottom Button
        const sec_bottom_button = document.getElementById('purchase-receipt-order-sec-button');
        const sec_bottom_button_content = frappe.render_template("bottom_button_sec");
        sec_bottom_button.innerHTML = sec_bottom_button_content;
    }
    
    show_specific_dynamic_content() {
        document.getElementById("ok-button").style.backgroundColor = this.colors.purchase_receipt;
        document.getElementById("action-button").textContent = "Einlagerung mit standart Frachtkosten";
        document.getElementById("action-button").style.backgroundColor = this.colors.purchase_receipt;
        document.getElementById("secondary-action-button").textContent = "Einlagerung mit manuellen Frachtkosten";
        document.getElementById("secondary-action-button").style.backgroundColor = this.colors.purchase_receipt_sec;
        document.getElementById("nav-title").textContent = this.order;
        this.show_dynamic_content()
    }
    
    get_order_items() {
        if (this.order) {
            frappe.call({
                'method': 'seg.seg.page.stock_management.stock_management.get_order_items',
                'args': {
                    'order': this.order
                },
                'callback': (response) => {
                    console.log("items: " + response.message);
                    this.items = response.message;
                    this.on_show();
                }
            });
        }
    }
    
    store_everything(order, submit) {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.store_everything',
            'args': {
                'order': order,
                'submit': submit
            },
            'callback': (response) => {
                if (response.message) {
                    if (response.message.success) {
                        this.show_success(response.message.message, "button-message");
                    }
                } else {
                    this.show_error("Beim einlagern ist ein Fehler aufgetreten.", "button-message");
                }
            }
        });
    }
    
    create_link_fields() {
        //Item
        const item_container = document.getElementById("article-input");

        this.item_link_field = frappe.ui.form.make_control({
            parent: item_container,
            df: {
                fieldtype: "Link",
                options: "Item",
                fieldname: "item",
                get_query: () => {
                    let po_items = this.items.map(item => item.item_code);
                    return {
                        filters: {
                            name: ["in", po_items]
                        }
                    };
                },
				change: () => {
                    document.activeElement.blur();
                    this.item = this.item_link_field.get_value();
				}
            },
            only_input: true
        });

        this.item_link_field.make();
        this.item_link_field.refresh();
    }
    
    //Handle Scan Input
    async handle_scan(scan_buffer) {
        console.log("Order");
        if (/^\d+$/.test(scan_buffer)) {
            this.item_dict;
            this.item_dict = await this.translate_item_barcode(scan_buffer);
            if (this.item_dict) {
                this.item_link_field.set_value(this.item_dict[0].item_code);
                const target_item = this.items.find(item => item.item_code === this.item_dict[0].item_code);
                document.getElementById("quantity-input").value = target_item.content.qty;
            } else {
                this.show_error("Artikel konnte nicht gefunden werden.", "item-input-message");
            }
        } else {
            this.show_error("Artikel konnte nicht gefunden werden.", "item-input-message");
        }
    }
}

//Purchase Receipt - Show Warehouse to Stock Items
class PurchaseReceiptItem extends PurchaseReceiptOrder {
	constructor(item, qty, parent_this, grandparent_this) {
		super('stock_enter_item', "Zielplatz");
        this.item = item;
        this.starting_qty = qty;
        this.item_dict;
        this.entry_warehouse;
        this.warehouse;
        this.parent_this = parent_this;
        this.grandparent_this = grandparent_this;
	}

	init() {
        this.get_item_and_warehouse_information(this.item);
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.grandparent_this.add_general_event_handlers()
        
        //Go back to Stock Enter Page <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(new PurchaseReceiptOrder('purchase_receipt_order', "Wareneingang", this.parent_this.order, this.grandparent_this));
		});
        
        //Cleare Warehouse
        document.getElementById("clear-warehouse").addEventListener("click", () => {
            const warehouseInput = document.getElementById("warehouse-input");

            this.wh_link_field.set_value("");
            this.wh_link_field.set_focus();
        });
        
        //Add Quantity
        document.getElementById("wh-qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //Remove Quantity
        document.getElementById("wh-qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Submit Stock Entry
		document.getElementById("wh-ok-button").addEventListener("click", () => {
            if (this.warehouse) {
                const quantity = document.getElementById("wh-quantity-input").value;
                this.create_stock_entry(this.item, this.warehouse, quantity, this.parent_this.order, true);
            } else {
                this.show_error("Bitte zuerst den Lagerplatz wählen.", "wh-message");
            }
		});
        
        //Create Stock Entry
		document.getElementById("action-button").addEventListener("click", () => {
            if (this.warehouse) {
                const quantity = document.getElementById("wh-quantity-input").value;
                this.create_stock_entry(this.item, this.warehouse, quantity, this.parent_this.order);
            } else {
                this.show_error("Bitte zuerst den Lagerplatz wählen.", "wh-message");
            }
		});
        
        document.querySelectorAll(".item-row").forEach(row => {
            row.addEventListener("click", () => {
                document.getElementById("wh-quantity-input").value = this.item_dict[0].content.qty;
            });
		});
    }
    
    show_subsections() {
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
        const list_section_content = frappe.render_template("items_list_without_counter", {'items': this.item_dict});
        list_section.innerHTML = list_section_content;
        
        //Show Warehouse Overview
        this.warehouses;
        this.get_item_warehouses(this.item)
        
        //Show Bottom Button
        const bottom_button = document.getElementById('stock-enter-item-button');
        const bottom_button_content = frappe.render_template("bottom_button");
        bottom_button.innerHTML = bottom_button_content;
    }
    
    show_specific_dynamic_content() {
        document.getElementById("wh-ok-button").style.backgroundColor = this.colors.purchase_receipt;
        document.getElementById("wh-quantity-input").value = this.starting_qty;
        document.getElementById("warehouse-input").value = this.default_warehouse;
        document.getElementById("nav-title").textContent = this.label;
        document.getElementById("action-button").textContent = "Einlagerung mit manuellen Frachtkosten";
        document.getElementById("action-button").style.backgroundColor = this.colors.purchase_receipt_sec;
        this.show_dynamic_content()
    }
    
    get_item_and_warehouse_information(item) {
        if (item) {
            frappe.call({
                'method': 'seg.seg.page.stock_management.stock_management.get_order_items',
                'args': {
                    'item': this.item,
                    'order': this.parent_this.order
                },
                'callback': (response) => {
                    this.item_dict = response.message;
                    console.log("Response: " + this.item_dict);
                    this.get_entry_warehouse()
                }
            });
        }
    }
    
    async get_item_warehouses(item) {
        if (item) {
            this.warehouses = await this.get_warehouse_overview(item);
            const warehouse_overview = document.getElementById('stock-enter-item-wh-overview');
            const warehouse_overview_content = frappe.render_template("warehouse_overview", {'warehouses': this.warehouses});
            warehouse_overview.innerHTML = warehouse_overview_content;
        }
    }
    
    create_stock_entry(item, warehouse, qty, order, submit=false) {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.create_single_receipt',
            'args': {
                'item_code': item,
                'target_warehouse': warehouse,
                'qty': qty,
                'order': order,
                'submit': submit
            },
            'callback': (response) => {
                if (response.message) {
                    if (response.message.success) {
                        this.show_success(response.message.message, "wh-message");
                    } else {
                        this.show_error(response.message.error, "wh-message");
                    }
                } else {
                    this.show_error("Beim einlagern ist ein Fehler aufgetreten.", "wh-message");
                }
            }
        });
    }
    
    get_entry_warehouse() {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.get_entry_warehouse',
            'args': {
                //no args yet
            },
            'callback': (response) => {
                if (response.message) {
                    this.entry_warehouse = response.message;
                    this.on_show();
                }
            }
        });
    }
    
    create_link_fields() {
        //From Warehouse
        const wh_container = document.getElementById("warehouse-input");

        this.wh_link_field = frappe.ui.form.make_control({
            parent: wh_container,
            df: {
                fieldtype: "Link",
                options: "Warehouse",
                fieldname: "warehouse",
				change: () => {
                    document.activeElement.blur();
                    //Save Entered Warehouse
                    this.warehouse = this.wh_link_field.get_value();
				}
            },
            only_input: true
        });
        
        this.wh_link_field.make();
        this.wh_link_field.refresh();
        this.wh_link_field.set_value(this.entry_warehouse);
    }
    
    async handle_scan(scan_buffer) {
        //~ if (/^\d+$/.test(scan_buffer)) {
            //~ this.item_dict;
            //~ this.item_dict = await this.translate_item_barcode(scan_buffer);
            //~ if (this.item_dict) {
                //~ this.item_link_field.set_value(this.item_dict[0].item_code);
            //~ } else {
                //~ this.show_error("Artikel konnte nicht gefunden werden.", "transfer-message");
            //~ }
        //~ } else {
            console.log("item");
            let warehouse = scan_buffer + " - SEG";
            this.wh_link_field.set_value(warehouse);
        //~ }
    }
}

//Stock Enter - Pick Item
class StockEnterPage extends StockManagementClass {
	constructor(key, label) {
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
        this.create_link_fields();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Home <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
		});
        
        //Close Stock Entry and Go to Home
		document.getElementById("action-button").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
		});
        
        //Delete Item Field
        document.getElementById("clear-article").addEventListener("click", () => {
            const articleInput = document.getElementById("article-input");

            articleInput.value = "";
            articleInput.focus();
        });
        
        //Add Quantity
        document.getElementById("qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //remove Quantity
        document.getElementById("qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Open Item Tab
		document.getElementById("ok-button").addEventListener("click", () => {
            let qty = document.getElementById("quantity-input").value;
            frappe.stock_management.load_tab(new StockEnterItem('stock_enter_item', "Zielplatz", this.item, qty, this));
		});
    }
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('stock-enter-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Item Input
        const item_input = document.getElementById('stock-enter-input');
        const item_input_content = frappe.render_template("item_input", {'title': this.label});
        item_input.innerHTML = item_input_content;
        
        //Show Item Table
        const list_section = document.getElementById('stock-enter-list');
        const list_section_content = frappe.render_template("items_list", {'items': this.items});
        list_section.innerHTML = list_section_content;
        
        //Show Bottom Button
        const bottom_button = document.getElementById('stock-enter-button');
        const bottom_button_content = frappe.render_template("bottom_button");
        bottom_button.innerHTML = bottom_button_content;
    }
    
    async get_entry_warehouse_items() {
        this.items = await this.create_item_dict_by_warehouse("entry_warehouse");
        this.on_show();
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
    
    update_stocked_amount(item_code, new_amount) {
        const target_item = this.items.find(item => item.item_code === item_code);
        target_item.content['stored_qty'] = target_item.content['stored_qty'] + new_amount;
        this.refresh_stocked_amount(item_code, target_item.content['qty'], target_item.content['stored_qty']);
    }
    
    refresh_stocked_amount(item_code, qty, new_amount) {
        const progress_div = document.getElementById(item_code + "_amount");
        progress_div.innerText = new_amount + "/" + qty;
    }
    
    create_link_fields() {
        //Item
        const item_container = document.getElementById("article-input");

        this.item_link_field = frappe.ui.form.make_control({
            parent: item_container,
            df: {
                fieldtype: "Link",
                options: "Item",
                fieldname: "item",
				change: () => {
                    document.activeElement.blur();
                    this.item = this.item_link_field.get_value();
				}
            },
            only_input: true
        });

        this.item_link_field.make();
        this.item_link_field.refresh();
    }
}

//Stock Enter - Pick To Warehouse
class StockEnterItem extends StockEnterPage {
	constructor(key, label, item, qty, parent_this) {
        console.log(item);
		super(key, label);
        this.item = item;
        this.starting_qty = qty;
        this.item_dict;
        this.parent_this = parent_this;
        this.warehouse;
	}

	init() {
        this.get_item_information(this.item);
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Stock Enter Page <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.stock_enter);
		});
        
        //Cleare Warehouse
        document.getElementById("clear-warehouse").addEventListener("click", () => {
            const warehouseInput = document.getElementById("warehouse-input");

            warehouseInput.value = "";
            warehouseInput.focus();
        });
        
        //Add Quantity
        document.getElementById("wh-qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //Remove Quantity
        document.getElementById("wh-qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Submit Stock Entry
		document.getElementById("wh-ok-button").addEventListener("click", () => {
            const quantity = document.getElementById("wh-quantity-input").value;
            this.create_stock_entry(this.item, this.warehouse, quantity)
		});
    }
    
    show_subsections() {
        console.log("show_subsections_item");
        console.log(this.item);
        console.log(this.item_dict);
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
        const list_section_content = frappe.render_template("stock_enter_item_list", {'items': this.item_dict});
        list_section.innerHTML = list_section_content;
        
        //Show Warehouse Overview
        this.warehouses;
        this.get_item_warehouses(this.item)
    }
    
    show_specific_dynamic_content() {
        document.getElementById("wh-ok-button").style.backgroundColor = this.colors.stock_enter;
        console.log(this.starting_qty);
        document.getElementById("wh-quantity-input").value = this.starting_qty;
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
                    console.log(response.message);
                    this.item_dict = response.message;
                    this.on_show();
                }
            });
        }
    }
    
    get_item_warehouses(item) {
        if (item) {
            frappe.call({
                'method': 'seg.seg.page.stock_management.stock_management.get_warehouse_overview',
                'args': {
                    'item': item
                },
                'callback': (response) => {
                    this.warehouses = response.message;
                    const warehouse_overview = document.getElementById('stock-enter-item-wh-overview');
                    const warehouse_overview_content = frappe.render_template("warehouse_overview", {'warehouses': this.warehouses});
                    warehouse_overview.innerHTML = warehouse_overview_content;
                }
            });
        }
    }
    
    create_stock_entry(item, warehouse, qty) {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.create_enter_stock_entry',
            'args': {
                'item': item,
                'target_warehouse': warehouse,
                'qty': qty
            },
            'callback': (response) => {
                console.log(response.message);
                if (response.message) {
                    if (response.message.success) {
                        console.log("sucess");
                        this.show_success("Artikel wurde erfolgreich eingelagert.", "wh-message");
                        this.parent_this.update_stocked_amount(item, qty);
                    } else {
                        console.log("error");
                        this.show_error(response.message.error, "wh-message");
                    }
                } else {
                    this.show_error("Beim einlagern ist ein Fehler aufgetreten.", "wh-message");
                }
            }
        });
    }
    
    //Create Link Fields
    create_link_fields() {
        //Item
        const wh_container = document.getElementById("warehouse-input");

        this.wh_link_field = frappe.ui.form.make_control({
            parent: wh_container,
            df: {
                fieldtype: "Link",
                options: "Warehouse",
                fieldname: "warehouse",
				change: () => {
                    document.activeElement.blur();
                    this.warehouse = this.wh_link_field.get_value();
				}
            },
            only_input: true
        });

        this.wh_link_field.make();
        this.wh_link_field.refresh();
    }
}

//Stock Transfer
class StockTransferPage extends StockManagementClass {
	constructor(key, label) {
		super(key, label);
	}

	init() {
		this.on_show()
	}

	on_show() {
        this.show_subsections();
        this.show_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('stock-transfer-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Stock Transfer Input
        const stock_transfer_input = document.getElementById('stock-transfer-input');
        const stock_transfer_content = frappe.render_template("stock_transfer_input", {'title': this.label});
        stock_transfer_input.innerHTML = stock_transfer_content;
    }
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Home <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
		});
        
        // Delete From Warehouse
        document.getElementById("clear-from-warehouse").addEventListener("click", () => {

            this.from_wh_link_field.set_value("");
            this.from_wh_link_field.set_focus();

        });


        // Delete To Warehouse
        document.getElementById("clear-to-warehouse").addEventListener("click", () => {

            this.to_wh_link_field.set_value("");
            this.to_wh_link_field.set_focus();

        });


        // Delete Item
        document.getElementById("clear-transfer-article").addEventListener("click", () => {

            this.item_link_field.set_value("");
            this.item_link_field.set_focus();

        });
        
        //Add Quantity
        document.getElementById("transfer-qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("transfer-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //remove Quantity
        document.getElementById("transfer-qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("transfer-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Restock Item
		document.getElementById("transfer-ok-button").addEventListener("click", () => {
            let qty = document.getElementById("transfer-quantity-input").value;
            if ((!this.item) || (!this.from_warehouse) || (!this.to_warehouse)) {
                this.show_error("Bitte zuerst alle Felder befüllen.", "transfer-message")
            } else {
                //Prepare Items
                let items = [{'item_code': this.item, 'qty': qty, 'from_warehouse': this.from_warehouse, 'to_warehouse': this.to_warehouse}]
                //Create Stock Entry
                this.create_stock_entry(items, "Material Transfer", "transfer-message");
            }
		});
        
    }
    
    //Show Dynamic Content
    show_dynamic_content() {
        document.getElementById("nav-title").textContent = this.label;
        document.getElementById("transfer-ok-button").style.backgroundColor = this.colors.stock_transfer;
        document.getElementById("nav-back").style.backgroundColor = this.colors.stock_transfer;
        document.getElementById("mobile-navbar").style.backgroundColor = this.colors.stock_transfer;
    }
    
    async display_items_and_warehouses() {
        const warehouse_overview = document.getElementById("stock-transfer-wh-overview");
        if (this.item) {
            //Get Item Dict
            this.item_dict = await this.create_item_dict(this.item);
            //Get Warehouse Information
            this.warehouses = await this.get_warehouse_overview(this.item_dict[0].item_code);
            warehouse_overview.style.display = "";
        } else {
            //Remove Information
            this.item_dict = []
            this.warehouses = []
            warehouse_overview.style.display = "none";
        }
        //Show Item Table
        const list_section = document.getElementById('stock-transfer-list');
        const list_section_content = frappe.render_template("item_list_without_qty", {'items': this.item_dict});
        list_section.innerHTML = list_section_content;
        
        //Show Warehouse Information
        const warehouse_overview_content = frappe.render_template("warehouse_overview", {'warehouses': this.warehouses});
        warehouse_overview.innerHTML = warehouse_overview_content;
    }
    
    //Check if an Item or Warehouse has been scanned and set value to the right field
    async handle_scan(scan_buffer) {
        if (/^\d+$/.test(scan_buffer)) {
            this.item_dict;
            this.item_dict = await this.translate_item_barcode(scan_buffer);
            if (this.item_dict) {
                this.item_link_field.set_value(this.item_dict[0].item_code);
            } else {
                this.show_error("Artikel konnte nicht gefunden werden.", "transfer-message");
            }
        } else {
            let warehouse = scan_buffer + " - SEG"
            if (!this.from_wh_link_field.get_value()) {
                this.from_wh_link_field.set_value(warehouse);
            } else {
                this.to_wh_link_field.set_value(warehouse);
            }
        }
    }
    
    create_link_fields() {
        //Item
        const item_container = document.getElementById("transfer-article-input");

        this.item_link_field = frappe.ui.form.make_control({
            parent: item_container,
            df: {
                fieldtype: "Link",
                options: "Item",
                fieldname: "item",
				change: () => {
                    document.activeElement.blur();
                    this.item = this.item_link_field.get_value();
                    //Show Items and Warehouses when Item has been scanned
                    this.display_items_and_warehouses()
				}
            },
            only_input: true
        });

        this.item_link_field.make();
        this.item_link_field.refresh();
        
        //From Warehouse
        const from_wh_container = document.getElementById("from-warehouse-input");

        this.from_wh_link_field = frappe.ui.form.make_control({
            parent: from_wh_container,
            df: {
                fieldtype: "Link",
                options: "Warehouse",
                fieldname: "from_warehouse",
				change: () => {
                    document.activeElement.blur();
                    //Show All Items on Warehouse, when Warehouse has been selected first
                    this.from_warehouse = this.from_wh_link_field.get_value();
                    if (!this.item) {
                        this.display_items_by_warehouse(this.from_warehouse);
                    }
                    
				}
            },
            only_input: true
        });

        this.from_wh_link_field.make();
        this.from_wh_link_field.refresh();
        
        //To Warehouse
        const to_wh_container = document.getElementById("to-warehouse-input");

        this.to_wh_link_field = frappe.ui.form.make_control({
            parent: to_wh_container,
            df: {
                fieldtype: "Link",
                options: "Warehouse",
                fieldname: "to_warehouse",
				change: () => {
                    document.activeElement.blur();
                    this.to_warehouse = this.to_wh_link_field.get_value();
				}
            },
            only_input: true
        });

        this.to_wh_link_field.make();
        this.to_wh_link_field.refresh();
    }
    
    async display_items_by_warehouse(warehouse) {
        if (warehouse) {
            this.item_dict = await this.create_item_dict_by_warehouse(warehouse);
        } else {
            this.item_dict = []
        }
        //Show Item Table
        const list_section = document.getElementById('stock-transfer-list');
        const list_section_content = frappe.render_template("items_list_without_counter", {'items': this.item_dict});
        list_section.innerHTML = list_section_content;
    }
    
}

//Picking Page
class PickingPage extends StockManagementClass {
	constructor(key, label) {
		super(key, label);
        this.picking_lists;
        this.selected_customer;
	}

	init() {
		this.get_open_picking_lists()
	}

	on_show() {
        this.show_subsections();
        this.add_event_listeners();
        this.create_link_fields();
        this.show_specific_dynamic_content();
	}
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('picking-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Picking Input
        const picking_input = document.getElementById('picking-input');
        const picking_content = frappe.render_template("picking_input", {'title': this.label});
        picking_input.innerHTML = picking_content;
        
        //Show Picking List Table
        this.display_picking_lists()
    }
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Home <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
		});
        
        //Delete PO Field
        document.getElementById("clear-picking-list").addEventListener("click", () => {
            this.picking_list_link_field.set_value("");
            this.picking_list_link_field.set_focus();
        });
        
        //Delete Supplier Field
        document.getElementById("clear-customer").addEventListener("click", () => {
        
            this.customer_link_field.set_value("");
            this.customer_link_field.set_focus();

        });
        
        //Open Pruchase Order Tab
		document.getElementById("picking-list-ok-button").addEventListener("click", () => {
            let picking_list = this.selected_picking_list ?? "";
            if (picking_list) {
                frappe.stock_management.load_tab(new PickingList('picking_list', "Artikel Kommissionieren", picking_list, this));
            } else {
                this.show_error("Bitte einen Rüstschein wählen", "picking-message");
            }
		});
    }
    
    //Show Dynamic Content specific for this Site
    show_specific_dynamic_content() {
        document.getElementById("picking-list-ok-button").style.backgroundColor = this.colors.picking;
        document.getElementById("nav-title").textContent = this.label;
        this.show_dynamic_content()
    }
    
    //Show Dynmic Content for whole Purchase Receipt Classes
    show_dynamic_content() {
        console.log("setting navbar color");
        document.getElementById("nav-back").style.backgroundColor = this.colors.picking;
        document.getElementById("mobile-navbar").style.backgroundColor = this.colors.picking;
    }
    
    get_open_picking_lists(refresh=false) {
        const customer = this.selected_customer ?? "";
        const picking_list = this.selected_picking_list ?? "";
        
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.get_open_picking_lists',
            'args': {
                'customer': customer,
                'picking_list': picking_list
            },
            'callback': (response) => {
                this.pickings_lists = response.message;
                if (!refresh) {
                    this.on_show();
                } else {
                    this.refresh_picking_list_list()
                }
            }
        });
    }
    
    create_link_fields() {
        //Picking List
        const picking_list_container = document.getElementById("picking-list-input");

        this.picking_list_link_field = frappe.ui.form.make_control({
            parent: picking_list_container,
            df: {
                fieldtype: "Link",
                options: "Picking List",
                fieldname: "picking_list",
                
                get_query: () => {
                    const filters = {
                        'docstatus': 1,
                        'status': "Open"
                    }
                    
                    if (this.selected_customer) {
                        filters.customer = this.selected_customer
                    }
                    
                    return {
                        filters: filters
                    };
                },
                
				change: () => {
                    this.selected_picking_list = this.picking_list_link_field.get_value();
                    document.activeElement.blur();
                    this.get_open_picking_lists(true)
				}
            },
            only_input: true
        });

        this.picking_list_link_field.make();
        this.picking_list_link_field.refresh();
        
        //Customer
		const customer_container = document.getElementById("customer-input");

		this.customer_link_field = frappe.ui.form.make_control({
			parent: customer_container,
			df: {
				fieldtype: "Link",
				options: "Customer",
				name: "customer",
				change: () => {
					this.selected_customer = this.customer_link_field.get_value();
                    document.activeElement.blur();
                    this.get_open_picking_lists(true)
				}
			},
			only_input: true
		});
        this.customer_link_field.make()
		this.customer_link_field.refresh();
    }
    
    refresh_picking_list_list() {
        this.display_picking_lists()
    }
    
    display_picking_lists() {
        const list_section = document.getElementById('picking-list');
        const list_section_content = frappe.render_template("picking_list_list", {'pickings_lists': this.pickings_lists});
        list_section.innerHTML = list_section_content;
    }
}

//Picking List - Show Items to pick
class PickingList extends PickingPage {
	constructor(key, label, picking_list, parent_this) {
		super(key, label);
        this.picking_list = picking_list;
        this.parent_this = parent_this;
	}

	init() {
        this.get_picking_list_items();
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Picking Page <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.picking);
		});
        
        //Cleare Item
        document.getElementById("clear-article").addEventListener("click", () => {
            const warehouseInput = document.getElementById("article-input");

            warehouseInput.value = "";
            warehouseInput.focus();
        });
        
        //Add Quantity
        document.getElementById("qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //remove Quantity
        document.getElementById("qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Submit Stock Entry
		document.getElementById("action-button").addEventListener("click", () => {
            console.log(this.item);
            console.log(this.picking_list);
            //~ this.create_delivery_note(this.order);
		});
        
        //Open Item Tab
		document.getElementById("ok-button").addEventListener("click", () => {
            if (this.item) {
                let qty = document.getElementById("quantity-input").value;
                frappe.stock_management.load_tab(new PickingListItem(this.item, qty, this, this.parent_this));
            } else {
                this.show_error("Bitte Artikel auswählen", "item-input-message");
            }
		});
        
    }
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('picking-list-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Item Input
        const item_input = document.getElementById('picking-list-input');
        const item_input_content = frappe.render_template("item_input", {'title': this.label});
        item_input.innerHTML = item_input_content;
        
        //Show Item Table
        const list_section = document.getElementById('picking-list-list');
        const list_section_content = frappe.render_template("items_list", {'items': this.items});
        list_section.innerHTML = list_section_content;
        
        //Show Bottom Button
        const bottom_button = document.getElementById('picking-list-button');
        const bottom_button_content = frappe.render_template("bottom_button", {'items': this.items});
        bottom_button.innerHTML = bottom_button_content;
    }
    
    show_specific_dynamic_content() {
        document.getElementById("ok-button").style.backgroundColor = this.colors.picking;
        document.getElementById("action-button").textContent = "Rüsten abschliessen";
        document.getElementById("action-button").style.backgroundColor = this.colors.picking;
        document.getElementById("nav-title").textContent = this.picking_list;
        this.show_dynamic_content()
    }
    
    get_picking_list_items() {
        if (this.picking_list) {
            frappe.call({
                'method': 'seg.seg.page.stock_management.stock_management.get_picking_list_items',
                'args': {
                    'picking_list': this.picking_list
                },
                'callback': (response) => {
                    this.items = response.message;
                    console.log(this.items);
                    this.on_show();
                }
            });
        }
    }
    
    create_link_fields() {
        //Item
        const item_container = document.getElementById("article-input");

        this.item_link_field = frappe.ui.form.make_control({
            parent: item_container,
            df: {
                fieldtype: "Link",
                options: "Item",
                fieldname: "item",
                get_query: () => {
                    let po_items = this.items.map(item => item.item_code);
                    return {
                        filters: {
                            name: ["in", po_items]
                        }
                    };
                },
				change: () => {
                    document.activeElement.blur();
                    this.item = this.item_link_field.get_value();
				}
            },
            only_input: true
        });

        this.item_link_field.make();
        this.item_link_field.refresh();
    }
}

//Purchase Receipt - Show Warehouse to Stock Items
class PickingListItem extends PickingList {
	constructor(item, qty, parent_this, grandparent_this) {
		super('picking_list_item', "Quellplatz");
        this.item = item;
        this.starting_qty = qty;
        this.item_dict;
        this.parent_this = parent_this;
        this.grandparent_this = grandparent_this;
	}

	init() {
        this.get_item_information(this.item);
	}

	on_show() {
        this.show_subsections();
        this.show_specific_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.grandparent_this.add_general_event_handlers()
        
        //~ //Go back to Stock Enter Page <- ZURÜCK ZU AKTUALISERTER ANSICHT
		//~ document.getElementById("nav-back").addEventListener("click", () => {
            //~ frappe.stock_management.load_tab(new PurchaseReceiptOrder('purchase_receipt_order', "Wareneingang", this.parent_this.order, this.grandparent_this));
		//~ });
        
        //Cleare Warehouse
        document.getElementById("clear-warehouse").addEventListener("click", () => {
            const warehouseInput = document.getElementById("warehouse-input");

            this.wh_link_field.set_value("");
            this.wh_link_field.set_focus();
        });
        
        //Add Quantity
        document.getElementById("wh-qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //Remove Quantity
        document.getElementById("wh-qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("wh-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Add picked items
		document.getElementById("wh-ok-button").addEventListener("click", () => {
            if (this.warehouse) {
                const quantity = document.getElementById("wh-quantity-input").value;
                this.add_picked_item(this.item, this.warehouse, quantity, this.parent_this)
            } else {
                this.show_error("Bitte Lagerplatz wählen.", "wh-message");
            }
		});
    }
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('picking-list-item-navbar');
        const header_menu_section_content = frappe.render_template("header_menu", {'title': this.label});
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Warehouse Input
        const item_input = document.getElementById('picking-list-item-input');
        const item_input_content = frappe.render_template("warehouse_input", {'title': this.label});
        item_input.innerHTML = item_input_content;
        
        //Show Single Item Table
        const list_section = document.getElementById('picking-list-item-list');
        const list_section_content = frappe.render_template("items_list_without_counter", {'items': this.item_dict});
        list_section.innerHTML = list_section_content;
        
        //Show Warehouse Overview
        this.warehouses;
        this.get_item_warehouses(this.item)
    }
    
    show_specific_dynamic_content() {
        document.getElementById("wh-ok-button").style.backgroundColor = this.colors.picking;
        document.getElementById("wh-quantity-input").value = this.starting_qty;
        document.getElementById("nav-title").textContent = this.label;
        this.show_dynamic_content()
    }
    
    get_item_information(item) {
        frappe.call({
            'method': 'seg.seg.page.stock_management.stock_management.get_picking_list_items',
            'args': {
                'picking_list': this.parent_this.picking_list,
                'item': this.item
            },
            'callback': (response) => {
                this.item_dict = response.message;
                this.on_show();
            }
        });
    }
    
    async get_item_warehouses(item) {
        if (this.item) {
            this.warehouses = await this.get_warehouse_overview(item);
            const warehouse_overview = document.getElementById('picking-list-item-wh-overview');
            const warehouse_overview_content = frappe.render_template("warehouse_overview", {'warehouses': this.warehouses});
            warehouse_overview.innerHTML = warehouse_overview_content;
        }
    }
    
    //~ create_stock_entry(item, warehouse, qty, order) {
        //~ frappe.call({
            //~ 'method': 'seg.seg.page.stock_management.stock_management.create_single_receipt',
            //~ 'args': {
                //~ 'item_code': item,
                //~ 'target_warehouse': warehouse,
                //~ 'qty': qty,
                //~ 'order': order
            //~ },
            //~ 'callback': (response) => {
                //~ if (response.message) {
                    //~ if (response.message.success) {
                        //~ this.show_success(response.message.message, "wh-message");
                    //~ } else {
                        //~ this.show_error(response.message.error, "wh-message");
                    //~ }
                //~ } else {
                    //~ this.show_error("Beim einlagern ist ein Fehler aufgetreten.", "wh-message");
                //~ }
            //~ }
        //~ });
    //~ }
    
    create_link_fields() {
        //Source Warehouse
        const wh_container = document.getElementById("warehouse-input");

        this.wh_link_field = frappe.ui.form.make_control({
            parent: wh_container,
            df: {
                fieldtype: "Link",
                options: "Warehouse",
                fieldname: "warehouse",
				change: () => {
                    document.activeElement.blur();
                    //Save Entered Warehouse
                    this.warehouse = this.wh_link_field.get_value();
				}
            },
            only_input: true
        });
        
        this.wh_link_field.make();
        this.wh_link_field.refresh();
    }
}

//Stock Transfer
class CreateSalesOrderPage extends StockManagementClass {
	constructor(key, label) {
		super(key, label);
        this.items = [];
        this.customer;
	}

	init() {
		this.on_show()
	}

	on_show() {
        this.show_subsections();
        this.show_dynamic_content();
        this.add_event_listeners();
        this.create_link_fields();
	}
    
    show_subsections() {
        //Show Navbar
        const header_menu_section = document.getElementById('create-order-navbar');
        const header_menu_section_content = frappe.render_template("header_menu");
        header_menu_section.innerHTML = header_menu_section_content;
        
        //Show Create Order Input
        const create_order_input = document.getElementById('create-order-input');
        const create_order_input_content = frappe.render_template("create_order_input");
        create_order_input.innerHTML = create_order_input_content;
        
        this.display_items()
        
        //Show Submit Button
        const create_order_button = document.getElementById('create-order-button');
        const create_order_button_content = frappe.render_template("bottom_button");
        create_order_button.innerHTML = create_order_button_content;
    }
    
    //Add Event Listeners
    add_event_listeners() {
        //Add General Event handlers
        this.add_general_event_handlers()
        
        //Go back to Home <-
		document.getElementById("nav-back").addEventListener("click", () => {
            frappe.stock_management.load_tab(frappe.stock_management.tab_instances.home);
		});
        
        // Delete Customer
        document.getElementById("clear-order-customer").addEventListener("click", () => {

            this.customer_link_field.set_value("");
            this.customer_link_field.set_focus();

        });
        
        // Delete Item
        document.getElementById("clear-order-article").addEventListener("click", () => {

            this.item_link_field.set_value("");
            this.item_link_field.set_focus();

        });
        
        // Delete Warehouse
        document.getElementById("clear-order-warehouse").addEventListener("click", () => {

            this.wh_link_field.set_value("");
            this.wh_link_field.set_focus();

        });
        
        //Add Quantity
        document.getElementById("order-qty-plus").addEventListener("click", () => {
            const quantityInput = document.getElementById("order-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            quantityInput.value = quantity + 1;
        });
        
        //remove Quantity
        document.getElementById("order-qty-minus").addEventListener("click", () => {
            const quantityInput = document.getElementById("order-quantity-input");

            const quantity = parseInt(quantityInput.value, 10) || 1;

            if (quantity > 1) {
                quantityInput.value = quantity - 1;
            }
        });
        
        //Add Item to Order
		document.getElementById("create-order-ok-button").addEventListener("click", () => {
            let item = this.item_link_field.get_value();
            let warehouse = this.wh_link_field.get_value();
            let qty = document.getElementById("order-quantity-input").value;
            if ((!item) || (!warehouse)) {
                this.show_error("Bitte zuerst alle Felder befüllen.", "order-message")
            } else {
                //Add Item to Items
                this.update_items(item, warehouse, qty);
            }
		});
        
        //Create Order
		document.getElementById("action-button").addEventListener("click", () => {
            this.create_sales_order();
		});
    }
    
    //Show Dynamic Content
    show_dynamic_content() {
        document.getElementById("nav-title").textContent = this.label;
        document.getElementById("create-order-ok-button").style.backgroundColor = this.colors.crete_sales_order;
        document.getElementById("nav-back").style.backgroundColor = this.colors.crete_sales_order;
        document.getElementById("mobile-navbar").style.backgroundColor = this.colors.crete_sales_order;
        document.getElementById("action-button").textContent = "Auftrag erstellen";
    }
    
    display_items() {
        //Show Item Table
        const list_section = document.getElementById('create-order-list');
        const list_section_content = frappe.render_template("items_list_without_counter", {'items': this.items});
        list_section.innerHTML = list_section_content;
    }
    
    async update_items(item_code, source_warehouse, qty) {
        //Create Item Dict
        let item_dict = await this.create_item_dict(item_code);
        console.log(item_dict);
        item_dict[0].content['warehouse'] = source_warehouse;
        item_dict[0].content['qty'] = qty;
        this.items.push(item_dict[0]);
        this.display_items();
    }
    
    //~ //Check if an Item or Warehouse has been scanned and set value to the right field
    //~ async handle_scan(scan_buffer) {
        //~ const input = document.getElementById("scan-test-input");
        //~ if (/^\d+$/.test(scan_buffer)) {
            //~ this.item_dict;
            //~ this.item_dict = await this.translate_item_barcode(scan_buffer);
            //~ if (this.item_dict) {
                //~ this.item_link_field.set_value(this.item_dict[0].item_code);
            //~ } else {
                //~ this.show_error("Artikel konnte nicht gefunden werden.", "transfer-message");
            //~ }
        //~ } else {
            //~ let warehouse = scan_buffer + " - SEG"
            //~ input.value = warehouse;
            //~ if (!this.from_wh_link_field.get_value()) {
                //~ this.from_wh_link_field.set_value(warehouse);
            //~ } else {
                //~ this.to_wh_link_field.set_value(warehouse);
            //~ }
        //~ }
    //~ }
    
    create_link_fields() {
        //Customer
        const customer_container = document.getElementById("create-order-customer-input");

        this.customer_link_field = frappe.ui.form.make_control({
            parent: customer_container,
            df: {
                fieldtype: "Link",
                options: "Customer",
                fieldname: "customer",
				change: () => {
                    document.activeElement.blur();
                    this.customer = this.to_wh_link_field.get_value();
				}
            },
            only_input: true
        });

        this.customer_link_field.make();
        this.customer_link_field.refresh();
        
        //Item
        const item_container = document.getElementById("order-article-input");

        this.item_link_field = frappe.ui.form.make_control({
            parent: item_container,
            df: {
                fieldtype: "Link",
                options: "Item",
                fieldname: "item",
				change: () => {
                    document.activeElement.blur();
				}
            },
            only_input: true
        });

        this.item_link_field.make();
        this.item_link_field.refresh();
        
        //From Warehouse
        const wh_container = document.getElementById("order-warehouse-input");

        this.wh_link_field = frappe.ui.form.make_control({
            parent: wh_container,
            df: {
                fieldtype: "Link",
                options: "Warehouse",
                fieldname: "from_warehouse",
				change: () => {
                    document.activeElement.blur();
				}
            },
            only_input: true
        });

        this.wh_link_field.make();
        this.wh_link_field.refresh();
    }
    
    create_sales_order() {
        if ((this.items) && (this.items.length > 0)) {
            console.log("Create Sales Order: " + this.items);
        } else {
            this.show_error("Bitte zuerst Artikel hinzufügen.", "button-message");
        }
    }
}
