"""
Whitelisted API methods for AWB generation on Delivery Note.
Uses Sales Order ID from Delivery Note Item's against_sales_order for API payload.
"""
import base64
import frappe
from frappe import _

from nexaflowtech_logistics.services.delhivery import DelhiveryService


@frappe.whitelist()
def create_delhivery_shipment(doc_name, shipment_width, shipment_height, shipment_length, weight):
	"""
	Create Delhivery shipment for a Delivery Note.
	Called after user submits the dimensions dialog.
	"""
	doc = frappe.get_doc("Delivery Note", doc_name)
	if doc.docstatus != 1:
		frappe.throw(_("Delivery Note must be submitted first."))

	if getattr(doc, "custom_awb_number", None):
		frappe.throw(_("AWB already generated: {0}").format(doc.custom_awb_number))

	# Validate mandatory dimensions from popup (weight in grams - Delhivery API expects grams)
	try:
		width = float(shipment_width)
		height = float(shipment_height)
		length = float(shipment_length)
		weight_grams = float(weight)
	except (TypeError, ValueError):
		frappe.throw(_("Invalid dimensions. Enter numeric values for width, height, length and weight."))

	if width <= 0 or height <= 0 or length <= 0 or weight_grams <= 0:
		frappe.throw(_("Width, height, length and weight must be greater than zero."))

	dimensions = {
		"shipment_width": str(int(width)),
		"shipment_height": str(int(height)),
		"shipment_length": str(int(length)),
		"weight": str(int(weight_grams)),  # API expects grams - user enters grams directly
	}

	service = DelhiveryService()
	result = service.create_shipment(doc, dimensions)

	if result.get("success"):
		if result.get("status") == "Pending AWB":
			doc.db_set("custom_shipment_status", "Pending AWB")
			doc.db_set("custom_courier_name", "Delhivery")
			doc.db_set("custom_awb_number", "")
			frappe.msgprint(
				_("Shipment uploaded successfully. Status: Pending AWB. Use Sync Status when ready."),
				indicator="blue",
				title=_("AWB Pending")
			)
		else:
			doc.db_set("custom_awb_number", result.get("awb"))
			doc.db_set("custom_courier_name", "Delhivery")
			doc.db_set("custom_shipment_status", result.get("status"))
			frappe.msgprint(
				_("Shipment created successfully. AWB: {0}").format(result.get("awb")),
				indicator="green",
				title=_("AWB Generated")
			)
	else:
		frappe.throw(_("Delhivery Error: {0}").format(result.get("error", "Unknown error")))


@frappe.whitelist()
def sync_delhivery_status(doc_name):
	"""Sync AWB status for a Delivery Note (when status is Pending AWB)."""
	doc = frappe.get_doc("Delivery Note", doc_name)
	service = DelhiveryService()
	result = service.sync_shipment(doc)

	if result.get("success"):
		doc.db_set("custom_awb_number", result.get("awb"))
		doc.db_set("custom_shipment_status", "Booked")
		frappe.msgprint(
			_("Sync successful. AWB: {0}").format(result.get("awb")),
			indicator="green",
			title=_("AWB Synced")
		)
		return True
	else:
		frappe.msgprint(
			_("Sync failed: {0}").format(result.get("error")),
			indicator="red",
			title=_("Sync Failed")
		)
		return False


@frappe.whitelist()
def download_delhivery_label(doc_name):
	"""Get packing slip label URL for Delivery Note AWB. Returns URL to open in browser."""
	doc = frappe.get_doc("Delivery Note", doc_name)
	awb = getattr(doc, "custom_awb_number", None)
	if not awb:
		frappe.throw(_("AWB number not found."))

	service = DelhiveryService()
	result = service.download_packing_slip(awb)

	if result.get("success"):
		# Delhivery returns pdf_url (pre-signed S3 link) - open directly, no File save
		if result.get("pdf_url"):
			return {"file_url": result["pdf_url"], "success": True}
		# Fallback: raw PDF content (rare) - save as File
		if result.get("content"):
			filename = "Label_{0}.pdf".format(awb)
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": filename,
				"attached_to_doctype": "Delivery Note",
				"attached_to_name": doc.name,
				"content": base64.b64encode(result.get("content")).decode("utf-8"),
				"is_private": 1,
			})
			file_doc.save()
			return {"file_url": file_doc.file_url, "success": True}
	frappe.throw(_("Download failed: {0}").format(result.get("error", "Unknown error")))
