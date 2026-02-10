import frappe
from nexaflowtech_logistics.nexaflowtech_logistics.background_jobs import create_delhivery_shipment_job, cancel_delhivery_shipment_job

def on_submit(doc, method):
	if should_create_shipment(doc):
		frappe.enqueue(
			create_delhivery_shipment_job,
			queue="long",
			doc_name=doc.name
		)

def on_cancel(doc, method):
	if doc.custom_awb_number:
		frappe.enqueue(
			cancel_delhivery_shipment_job,
			queue="long",
			doc_name=doc.name
		)

def should_create_shipment(doc):
	# Add any specific logic checks here, e.g. check if shipping address is present
	# or if the customer group matches criteria
	if not doc.shipping_address_name:
		frappe.msgprint("Warning: No Shipping Address specific. Delhivery shipment creation might fail.")
		return False
	return True
