# Copyright (c) 2017-2021, libracore AG and Contributors
# License: GNU General Public License v3. See license.txt

# customisation for total weight calculation
import frappe
import json
import six

@frappe.whitelist()
def get_total_weight(items, qtys, kgperL=1.5):
	total_weight = 0
	if isinstance(items, six.string_types):
		items = json.loads(items)
	if isinstance(qtys, six.string_types):
		qtys = json.loads(qtys)
	i = 0
	while i < len(items):
		doc = frappe.get_doc("Item", items[i])
		if doc != None:
			if doc.weight_per_unit > 0 and doc.has_weight:
				if doc.weight_uom == "kg":
					total_weight += qtys[i] * doc.weight_per_unit
				elif doc.weight_uom == "L":
					# make sure, tabItem contains custom field (float) density!
					total_weight += qtys[i] * doc.density * doc.weight_per_unit
		i += 1
	return { 'total_weight': total_weight }
