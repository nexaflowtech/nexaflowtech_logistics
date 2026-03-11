// AWB functionality moved to Delivery Note. No custom buttons on Sales Order.
frappe.ui.form.on("Sales Order", {
	refresh: function (frm) {
		// Reserved for any future Sales Order customizations
	}
});
