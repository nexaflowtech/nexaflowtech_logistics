frappe.ui.form.on("Delivery Note", {
	refresh: function (frm) {
		if (frm.doc.docstatus !== 1) return;

		var has_awb = frm.doc.custom_awb_number;
		var pending_awb = frm.doc.custom_shipment_status === "Pending AWB";

		if (!has_awb) {
			if (pending_awb) {
				frm.add_custom_button(__("Sync Status"), function () {
					frappe.call({
						method: "nexaflowtech_logistics.api.delivery_note_awb.sync_delhivery_status",
						args: { doc_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Syncing AWB Status..."),
						callback: function (r) {
							if (!r.exc) {
								frm.reload_doc();
								frappe.show_alert({ message: __("AWB synced successfully"), indicator: "green" }, 5);
							}
						}
					});
				}, __("Delhivery"));
			} else {
				frm.add_custom_button(__("Get AWB"), function () {
					open_awb_dialog(frm);
				}, __("Delhivery"));
			}
		} else {
			frm.add_custom_button(__("Download Label"), function () {
				frappe.call({
					method: "nexaflowtech_logistics.api.delivery_note_awb.download_delhivery_label",
					args: { doc_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Downloading Label..."),
					callback: function (r) {
						if (!r.exc && r.message && r.message.file_url) {
							window.open(r.message.file_url, "_blank");
							frappe.show_alert({ message: __("Label downloaded successfully"), indicator: "green" }, 5);
						}
					}
				});
			}, __("Delhivery"));
		}
	}
});

function open_awb_dialog(frm) {
	var d = new frappe.ui.Dialog({
		title: __("Shipment Dimensions"),
		fields: [
			{
				fieldname: "shipment_width",
				fieldtype: "Float",
				label: __("Width (cm)"),
				reqd: 1,
				description: __("Mandatory for API payload")
			},
			{
				fieldname: "shipment_height",
				fieldtype: "Float",
				label: __("Height (cm)"),
				reqd: 1
			},
			{
				fieldname: "shipment_length",
				fieldtype: "Float",
				label: __("Length (cm)"),
				reqd: 1
			},
			{
				fieldname: "weight",
				fieldtype: "Float",
				label: __("Weight (grams)"),
				reqd: 1,
				description: __("Enter weight in grams. Delhivery API expects grams.")
			}
		],
		primary_action_label: __("Get AWB"),
		primary_action: function (values) {
			if (!values.shipment_width || !values.shipment_height || !values.shipment_length || !values.weight) {
				frappe.msgprint(__("Please enter width, height, length and weight."), { indicator: "red" });
				return;
			}
			d.hide();
			frappe.call({
				method: "nexaflowtech_logistics.api.delivery_note_awb.create_delhivery_shipment",
				args: {
					doc_name: frm.doc.name,
					shipment_width: values.shipment_width,
					shipment_height: values.shipment_height,
					shipment_length: values.shipment_length,
					weight: values.weight
				},
				freeze: true,
				freeze_message: __("Generating AWB..."),
				callback: function (r) {
					if (!r.exc) {
						frm.reload_doc();
						frappe.show_alert({ message: __("AWB generated successfully"), indicator: "green" }, 5);
					}
				}
			});
		}
	});
	d.show();
}
