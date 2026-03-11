import frappe
from nexaflowtech_logistics.services.delhivery import DelhiveryService


def check_shipment_status():
	"""
	Scheduled task to check status of active shipments (Delivery Notes with AWB).
	"""
	active_delivery_notes = frappe.get_all(
		"Delivery Note",
		filters={
			"custom_awb_number": ["is", "set"],
			"custom_shipment_status": ["not in", ["Delivered", "Cancelled", "RTO Delivered"]],
			"docstatus": 1
		},
		fields=["name", "custom_awb_number", "custom_shipment_status"]
	)

	if not active_delivery_notes:
		return

	service = DelhiveryService()

	for dn in active_delivery_notes:
		try:
			track_info = service.track_shipment(dn.custom_awb_number)
			if track_info and track_info.get("ShipmentData"):
				shipment_data = track_info.get("ShipmentData", [])
				if shipment_data:
					latest_status = shipment_data[0].get("Shipment", {}).get("Status", {}).get("Status")
					if latest_status and latest_status != dn.custom_shipment_status:
						frappe.db.set_value("Delivery Note", dn.name, "custom_shipment_status", latest_status)
						frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				"Failed to track Delivery Note {0}: {1}".format(dn.name, str(e)),
				"Shipment Tracking"
			)
