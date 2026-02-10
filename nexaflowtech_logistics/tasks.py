import frappe
from nexaflowtech_logistics.nexaflowtech_logistics.services.delhivery import DelhiveryService

def check_shipment_status():
	"""
	Scheduled task to check status of active shipments.
	"""
	# Get all Sales Orders with AWB and status not Delivered/Cancelled
	active_orders = frappe.get_all(
		"Sales Order",
		filters={
			"custom_awb_number": ["is", "set"],
			"custom_shipment_status": ["not in", ["Delivered", "Cancelled", "RTO Delivered"]],
			"docstatus": 1
		},
		fields=["name", "custom_awb_number", "custom_shipment_status"]
	)

	if not active_orders:
		return

	service = DelhiveryService()
	
	for order in active_orders:
		try:
			track_info = service.track_shipment(order.custom_awb_number)
			
			if track_info and track_info.get("ShipmentData"):
				# Parse Delhivery Tracking Response
				# Structure varies, typically ShipmentData is a list
				shipment_data = track_info.get("ShipmentData", [])
				if shipment_data:
					latest_status = shipment_data[0].get("Shipment", {}).get("Status", {}).get("Status")
					
					if latest_status and latest_status != order.custom_shipment_status:
						frappe.db.set_value("Sales Order", order.name, "custom_shipment_status", latest_status)
						
						# Logic to update Delivery Note if exists
						# ...
						
						frappe.db.commit()
						
		except Exception as e:
			frappe.log_error(f"Failed to track order {order.name}: {str(e)}", "Shipment Tracking")
