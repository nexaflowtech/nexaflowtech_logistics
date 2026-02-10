import frappe
from nexaflowtech_logistics.nexaflowtech_logistics.services.delhivery import DelhiveryService

def create_delhivery_shipment_job(doc_name):
	try:
		doc = frappe.get_doc("Sales Order", doc_name)
		service = DelhiveryService()
		result = service.create_shipment(doc)
		
		if result.get("success"):
			doc.db_set("custom_awb_number", result.get("awb"))
			doc.db_set("custom_courier_name", result.get("courier"))
			doc.db_set("custom_shipment_status", result.get("status"))
			
			# Create Delivery Note Logic (Optional per requirement, usually integrated here)
			# create_delivery_note(doc)
			
			frappe.msgprint(f"Delhivery Shipment Created: AWB {result.get('awb')}")
		else:
			frappe.log_error(f"Delhivery Shipment Creation Failed: {result.get('error')}", "Delhivery Job")
			# We can create a ToDo or Notification for the user here
			frappe.msgprint(f"Delhivery Shipment Creation Failed: {result.get('error')}", indicator="red")

	except Exception as e:
		frappe.log_error(f"Background Job Error: {str(e)}", "nexaflowtech_logistics")

def cancel_delhivery_shipment_job(doc_name):
	try:
		doc = frappe.get_doc("Sales Order", doc_name)
		if doc.custom_awb_number:
			service = DelhiveryService()
			result = service.cancel_shipment(doc.custom_awb_number)
			
			if result.get("status") == "Success" or result.get("success"): # Check API specific success flag
				doc.db_set("custom_shipment_status", "Cancelled")
				frappe.msgprint(f"Delhivery Shipment Cancelled for AWB {doc.custom_awb_number}")
			else:
				frappe.log_error(f"Delhivery Cancellation Failed: {result}", "Delhivery Job")
				frappe.msgprint(f"Failed to cancel Delhivery Shipment: {result}", indicator="orange")
	except Exception as e:
		frappe.log_error(f"Background Job Error (Cancel): {str(e)}", "nexaflowtech_logistics")
