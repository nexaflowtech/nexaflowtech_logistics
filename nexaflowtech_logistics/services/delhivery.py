import frappe
import requests
import json
from frappe import _

class DelhiveryService:
	def __init__(self):
		self.settings = frappe.get_single("Logistics Settings")
		if not self.settings.enable_delhivery:
			frappe.throw(_("Delhivery integration is disabled in Logistics Settings"))
		
		# User specified no client_id, and provided strict curl example for token
		self.api_token = self.settings.get_password("api_token")
		self.base_url = self.settings.base_url or "https://track.delhivery.com"
		self.warehouse_name = self.settings.warehouse_name
		self.pickup_location = self.settings.pickup_location

	def create_shipment(self, doc, dimensions=None):
		"""
		Create a shipment in Delhivery using the strictly formatted payload.
		Endpoint: /api/cmu/create.json
		Payload: format=json&data={JSON}
		For Delivery Note, dimensions must contain shipment_width, shipment_height, weight (grams).
		"""
		url = f"{self.base_url}/api/cmu/create.json"
		
		# Prepare payload (dimensions required when doc is Delivery Note)
		try:
			payload_data = self._prepare_shipment_payload(doc, dimensions)
		except Exception as e:
			frappe.log_error(f"Payload Creation Error: {str(e)}", "Delhivery Integration")
			return {"success": False, "error": f"Payload Error: {str(e)}"}

		# Headers as per user request
		headers = {
			"Authorization": f"Token {self.api_token}"
		}
		
		# The API expects 'format=json' and 'data=<json_string>'
		body = {
			"format": "json",
			"data": json.dumps(payload_data)
		}

		# log entry init
		log_status = "Error"
		error_msg = ""
		awb = None
		response_data = None

		try:
			response = requests.post(url, data=body, headers=headers)
			# standard requests check
			# Note: Delhivery might return 200 even for logical errors, handled below.
			if response.status_code != 200:
				error_msg = f"HTTP Error {response.status_code}: {response.text}"
			else:
				response_data = response.json()
				
				# Check for success based on typical Delhivery CMU response
				# We ONLY want 'packages' with 'waybill'.
				# 'upload_wbn' is the upload ID, NOT the AWB. ignoring it.
				
				if response_data.get("packages") and len(response_data.get("packages")) > 0:
					package = response_data.get("packages")[0]
					
					# explicit check for 'waybill'
					if package.get("waybill"):
						awb = package.get("waybill")
						# Check if it looks like a UPL ID (just in case API changes behavior, but UPL is usually 'upload_wbn')
						if awb.startswith("UPL"):
							# If the API incorrectly put the upload ID in waybill field (unlikely but possible based on user report)
							# we treat it as failure/pending. But user says "actual look like this but in set field look like this UPL..."
							# This implies we were grabbing wrong field previously.
							pass 
						else:
							log_status = "Success"
					else:
						# Success=True but no waybill in package?
						error_msg = package.get("remarks") or "No waybill generated."
				
				else:
					# No packages returned. Check for top-level error
					error_msg = response_data.get("rmk") or response_data.get("error") or "Unknown error from Delhivery."
					if not error_msg and response_data.get("success"):
						# Case where success=True but no packages. Async upload? structure mismatch?
						# User requested "Pending AWB" state here.
						log_status = "Pending"
						error_msg = "Order Uploaded. Awaiting AWB generation."

		except Exception as e:
			error_msg = str(e)
			frappe.log_error(f"Delhivery Shipment Network Error: {str(e)}", "Delhivery Integration")

		# Create Delivery Log (use order ref for logging: SO name when from DN, else doc.name)
		order_ref = self._get_order_reference(doc)
		self._create_delivery_log(order_ref, payload_data, response_data, log_status, awb, error_msg)

		if log_status == "Success":
			return {
				"success": True,
				"awb": awb,
				"courier": "Delhivery",
				"status": "Booked",
				"response": response_data
			}
		elif log_status == "Pending":
			return {
				"success": True,
				"awb": None,
				"courier": "Delhivery",
				"status": "Pending AWB",
				"response": response_data
			}
		else:
			return {
				"success": False,
				"error": error_msg,
				"response": response_data
			}

	def sync_shipment(self, doc):
		"""
		Check status of a shipment by Reference ID (Order Name) to get the AWB.
		Endpoint: /api/v1/packages/json/?ref_ids=<ORDER_NAME>
		For Delivery Note, ref_id is the Sales Order from against_sales_order.
		"""
		url = f"{self.base_url}/api/v1/packages/json/"
		ref_id = self._get_order_reference(doc)
		params = {"ref_ids": ref_id}
		headers = {
			"Authorization": f"Token {self.api_token}",
			"Content-Type": "application/json"
		}
		
		log_status = "Error"
		error_msg = ""
		response_data = None
		awb = None
		
		try:
			response = requests.get(url, params=params, headers=headers)
			response.raise_for_status()
			response_data = response.json()
			
			# Response format: {"packages": [...]}
			if response_data.get("packages") and len(response_data.get("packages")) > 0:
				package = response_data.get("packages")[0]
				if package.get("waybill") and not package.get("waybill").startswith("UPL"):
					awb = package.get("waybill")
					log_status = "Success"
				else:
					error_msg = f"Status: {package.get('status', 'Unknown')}. Remarks: {package.get('remarks', 'No remarks')}"
			else:
				# If we search by ref_ids and get nothing, it might not be processed yet or invalid.
				error_msg = "No package found with this Reference ID."
				
		except Exception as e:
			error_msg = str(e)
			frappe.log_error(f"Delhivery Sync Error: {str(e)}", "Delhivery Integration")

		# Log this check if meaningful (or maybe only if successful/error)
		self._create_delivery_log(ref_id, {"action": "sync_status", "ref_id": ref_id}, response_data, log_status, awb, error_msg)
		
		if log_status == "Success":
			return {
				"success": True,
				"awb": awb,
				"status": "Booked",
				"response": response_data
			}
		else:
			return {
				"success": False,
				"error": error_msg
			}

	def _get_order_reference(self, doc):
		"""Return the order reference for API (ref_ids / order in payload). Delivery Note uses SO from items."""
		if doc.doctype == "Delivery Note":
			for item in (doc.items or []):
				if getattr(item, "against_sales_order", None):
					return item.against_sales_order
			frappe.throw(_("No linked Sales Order found in Delivery Note items. Set against_sales_order on at least one row."))
		return doc.name

	def _create_delivery_log(self, sales_order, request_payload, response_payload, status, awb, error):
		try:
			log = frappe.get_doc({
				"doctype": "Delivery Log",
				"sales_order": sales_order,
				"status": status,
				"awb_number": awb,
				"error_message": error,
				"request_payload": json.dumps(request_payload, indent=2) if request_payload else "",
				"response_payload": json.dumps(response_payload, indent=2) if response_payload else ""
			})
			log.insert(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Failed to create Delivery Log: {str(e)}", "Delhivery Integration")

	def _prepare_shipment_payload(self, doc, dimensions=None):
		# Use customer_address from Delivery Note (or other doc), not shipping_address_name
		if not getattr(doc, "customer_address", None):
			frappe.throw(_("Customer Address is required"))

		address = frappe.get_doc("Address", doc.customer_address)
		if not address.pincode:
			frappe.throw(_("Customer Address Pincode is required"))

		order_ref = self._get_order_reference(doc)
		
		product_descriptions = []
		total_qty = 0.0
		total_weight_grams = 0.0
		
		for item in doc.items:
			desc = item.item_name or item.item_code
			if desc not in product_descriptions:
				product_descriptions.append(desc)
			total_qty += item.qty
			w = getattr(item, "weight_per_unit", None) or 0.5
			total_weight_grams += (w * item.qty) * 1000

		products_desc_str = ", ".join(product_descriptions)
		if len(products_desc_str) > 100:
			products_desc_str = products_desc_str[:97] + "..."

		if dimensions and "shipment_width" in dimensions and "shipment_height" in dimensions and "weight" in dimensions:
			shipment_width = dimensions["shipment_width"]
			shipment_height = dimensions["shipment_height"]
			shipment_length = dimensions.get("shipment_length") or "10"
			weight_str = dimensions["weight"]
		else:
			shipment_width = "10"
			shipment_height = "10"
			shipment_length = "10"
			weight_str = str(int(total_weight_grams))

		payment_mode = "Prepaid"
		cod_amount = "0.00"
		is_cod = False
		if getattr(doc, "is_cod", None):
			is_cod = True
		elif getattr(doc, "payment_terms_template", None):
			try:
				term_template = frappe.get_doc("Payment Terms Template", doc.payment_terms_template)
				if term_template and ("COD" in (term_template.template_name or "").upper() or "CASH" in (term_template.template_name or "").upper()):
					is_cod = True
			except Exception:
				pass
		if is_cod:
			payment_mode = "COD"
			cod_amount = str(float(getattr(doc, "rounded_total", 0) or 0))

		pickup_loc_name = self.pickup_location
		phone = (address.phone or getattr(doc, "contact_mobile", None) or getattr(doc, "contact_phone", None) or "").strip()
		if not phone:
			phone = "9999999999"

		payload = {
			"shipments": [
				{
					"name": doc.customer_name or getattr(doc, "contact_person", None) or "Customer",
					"add": self._format_address(address),
					"pin": address.pincode,
					"city": address.city,
					"state": address.state,
					"country": address.country or "India",
					"phone": phone,
					"order": order_ref,
					"payment_mode": payment_mode,
					"products_desc": products_desc_str,
					"quantity": str(int(total_qty)),
					"total_amount": str(float(getattr(doc, "rounded_total", 0) or 0)),
					"cod_amount": cod_amount,
					"shipment_width": shipment_width,
					"shipment_height": shipment_height,
					"shipment_length": shipment_length,
					"weight": weight_str,
					"shipping_mode": "Surface"
				}
			],
			"pickup_location": {
				"name": pickup_loc_name
			}
		}
		return payload

	def _format_address(self, address):
		parts = [address.address_line1, address.address_line2]
		return ", ".join([p for p in parts if p])

	def track_shipment(self, awb):
		"""
		Track shipment strictly using:
		GET /api/v1/packages/json/?waybill=<AWB>
		"""
		url = f"{self.base_url}/api/v1/packages/json/"
		params = {"waybill": awb}
		headers = {
			"Authorization": f"Token {self.api_token}",
			"Content-Type": "application/json"
		}
		
		try:
			response = requests.get(url, params=params, headers=headers)
			response.raise_for_status()
			return response.json()
		except Exception as e:
			frappe.log_error(f"Delhivery Track Error: {str(e)}", "Delhivery Integration")
			return None

	def download_packing_slip(self, awb):
		"""
		Get packing slip label URL from Delhivery.
		Step 1: GET /api/p/packing_slip?wbns=<AWB>&pdf=true&pdf_size=4R
		        Returns JSON: {"packages":[{"pdf_download_link":"https://..."}]}
		Step 2: Return pdf_download_link - client opens URL directly (avoids PDF validation issues).
		Postman: (1) GET packing_slip API -> (2) Copy pdf_download_link -> (3) GET that URL for PDF.
		"""
		url = f"{self.base_url}/api/p/packing_slip"
		params = {
			"wbns": awb,
			"pdf": "true",
			"pdf_size": "4R"
		}
		headers = {
			"Authorization": f"Token {self.api_token}"
		}

		try:
			response = requests.get(url, params=params, headers=headers)
			response.raise_for_status()

			content_type = response.headers.get("Content-Type", "") or ""
			if "application/json" in content_type or (response.text or "").strip().startswith("{"):
				data = response.json()
				packages = data.get("packages") or []
				if not packages:
					return {"success": False, "error": _("No label link in Delhivery response.")}
				pdf_link = packages[0].get("pdf_download_link")
				if not pdf_link:
					return {"success": False, "error": _("PDF download link not found in Delhivery response.")}
				# Return URL directly - client opens in new tab. Avoids Frappe File PDF validation.
				return {"success": True, "pdf_url": pdf_link}
			else:
				# Fallback: API returns raw PDF
				content = response.content or b""
				if content.startswith(b"%PDF"):
					return {"success": True, "content": content, "content_type": "application/pdf"}
				return {"success": False, "error": _("Unexpected response from Delhivery.")}
		except requests.exceptions.RequestException as e:
			frappe.log_error("Delhivery Label Error: {0}".format(str(e)), "Delhivery Integration")
			return {"success": False, "error": str(e)}
		except Exception as e:
			frappe.log_error("Delhivery Label Error: {0}".format(str(e)), "Delhivery Integration")
			return {"success": False, "error": str(e)}
