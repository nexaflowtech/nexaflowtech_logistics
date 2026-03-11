import frappe
from nexaflowtech_logistics.services.delhivery import DelhiveryService


def update_tracking_status():
	"""
	Scheduled job to update status of all active shipments.
	Fetches Delivery Notes with AWB that are not Delivered/Cancelled/RTO.
	"""
	active_delivery_notes = frappe.get_all(
		"Delivery Note",
		filters={
			"custom_awb_number": ["is", "set"],
			"docstatus": 1,
			"custom_shipment_status": ["not in", ["Delivered", "Cancelled", "RTO Delivered", "RTO"]]
		},
		fields=["name", "custom_awb_number", "custom_shipment_status"]
	)

	if not active_delivery_notes:
		return

	service = DelhiveryService()
	count = 0

	for dn in active_delivery_notes:
		try:
			data = service.track_shipment(dn.custom_awb_number)
			if data and data.get("ShipmentData"):
				shipments = data.get("ShipmentData", [])
				if shipments:
					shipment_info = shipments[0].get("Shipment")
					if shipment_info:
						current_status = shipment_info.get("Status", {}).get("Status")
						if not current_status:
							current_status = shipment_info.get("Status")
						if current_status and current_status != dn.custom_shipment_status:
							frappe.db.set_value("Delivery Note", dn.name, "custom_shipment_status", current_status)
							count += 1
		except Exception as e:
			frappe.log_error(
				"Tracking Update Failed for {0}: {1}".format(dn.name, str(e)),
				"Delhivery Background Job"
			)

	if count > 0:
		frappe.db.commit()

