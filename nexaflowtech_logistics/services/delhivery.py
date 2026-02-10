import frappe
import requests
import json
from frappe import _

class DelhiveryService:
	def __init__(self):
		self.settings = frappe.get_single("Logistics Settings")
		if not self.settings.enable_delhivery:
			frappe.throw(_("Delhivery integration is disabled in Logistics Settings"))
		
		self.client_id = self.settings.client_id
		self.api_token = self.settings.get_password("api_token")
		self.base_url = self.settings.base_url
		self.warehouse_name = self.settings.warehouse_name
		self.pickup_location = self.settings.pickup_location

	def create_shipment(self, doc):
		"""
		Create a shipment in Delhivery for the given Sales Order document.
		"""
		# Updated endpoint as per user request
		url = f"{self.base_url}/api/cmu/create.json"
		
		payload = self._prepare_shipment_payload(doc)
		# User request shows 'Authorization: Token XXXXXX'
		headers = {
			"Authorization": f"Token {self.api_token}",
			"Content-Type": "application/json",
			"Accept": "application/json"
		}
		
		try:
			# fl=true is often used in Delhivery to flatten response, but not in user curl
			# The user curl uses --data 'format=json&data={...}'
			# We will replicate this structure
			
			data_payload = {
				"format": "json",
				"data": json.dumps(payload)
			}

			response = requests.post(url, data=data_payload, headers=headers)
			response.raise_for_status()
			data = response.json()
			
			# Check for success in the response structure
			# The response structure might vary, but typically it returns a list of packages or a success flag
			if data.get("success") or data.get("packages"):
				packages = data.get("packages", [])
				if packages:
					# Assuming the first package has the waybill
					awb = packages[0].get("waybill")
					return {
						"success": True,
						"awb": awb,
						"courier": "Delhivery",
						"status": "Booked",
						"response": data
					}
				elif data.get("upload_wbn"): # Some APIs return this
					return {
						"success": True,
						"awb": data.get("upload_wbn"),
						"courier": "Delhivery",
						"status": "Booked",
						"response": data
					}
				else:
					return {
						"success": False,
						"error": "No waybill returned in response",
						"response": data
					}
			else:
				# Attempt to extract error message
				error_msg = data.get("rmk") or data.get("error") or "Unknown error from Delhivery"
				return {
					"success": False,
					"error": error_msg,
					"response": data
				}

		except Exception as e:
			frappe.log_error(f"Delhivery Shipment Creation Failed: {str(e)}", "Delhivery Integration")
			return {
				"success": False,
				"error": str(e)
			}

	def _prepare_shipment_payload(self, doc):
		"""
		Prepare the JSON payload for Delhivery Shipment.
		"""
		if not doc.shipping_address_name:
			frappe.throw(_("Shipping Address is missing in Sales Order"))
			
		address = frappe.get_doc("Address", doc.shipping_address_name)
		
		# Calc total weight
		total_weight_grams = 0
		for item in doc.items:
			# weight_per_unit assumed in kg, convert to grams
			weight = (item.weight_per_unit or 0.5) * item.qty
			total_weight_grams += weight * 1000
			
		# Prepare payload matching user's structure
		shipment_data = {
			"shipments": [
				{
					"name": doc.customer_name,
					"add": address.address_line1 + " " + (address.address_line2 or ""),
					"pin": address.pincode,
					"city": address.city,
					"state": address.state,
					"country": address.country if address.country else "India",
					"phone": address.phone or doc.contact_phone,
					"order": doc.name,
					"payment_mode": "COD" if "COD" in (doc.payment_terms_template or "") else "Prepaid",
					"return_pin": "",
					"return_city": "",
					"return_phone": "",
					"return_add": "",
					"return_state": "",
					"return_country": "",
					"products_desc": "Shipment for " + doc.name,
					"hsn_code": "",
					"cod_amount": str(doc.rounded_total) if "COD" in (doc.payment_terms_template or "") else "",
					"order_date": str(doc.transaction_date) if doc.transaction_date else None,
					"total_amount": str(doc.rounded_total),
					"seller_add": self.pickup_location,
					"seller_name": self.warehouse_name,
					"seller_inv": "",
					"quantity": str(int(doc.total_qty)),
					"waybill": "",
					"shipment_width": "100", # Default or fetch from settings/item
					"shipment_height": "100",
					"weight": str(int(total_weight_grams)),
					"shipping_mode": "Surface",
					"address_type": ""
				}
			],
			"pickup_location": {
				"name": self.warehouse_name # Matching "warehouse_name" in user example
			}
		}
		return shipment_data

	def track_shipment(self, awb):
		# User provided: https://staging-express.delhivery.com/api/v1/packages/json/?waybill=...&ref_ids=
		url = f"{self.base_url}/api/v1/packages/json/"
		params = {
			"waybill": awb,
			"ref_ids": ""
		}
		headers = {
			"Authorization": f"Token {self.api_token}",
			"Content-Type": "application/json"
		}
		try:
			response = requests.get(url, params=params, headers=headers)
			response.raise_for_status()
			return response.json()
		except Exception as e:
			frappe.log_error(f"Delhivery Tracking Failed: {str(e)}", "Delhivery Integration")
			return None

	def download_packing_slip(self, awb):
		"""
		Download shipping label/packing slip.
		User provided: https://staging-express.delhivery.com/api/p/packing_slip?wbns=...&pdf=true&pdf_size=4R
		"""
		url = f"{self.base_url}/api/p/packing_slip"
		params = {
			"wbns": awb,
			"pdf": "true",
			"pdf_size": "4R"
		}
		headers = {
			"Authorization": f"Token {self.api_token}",
			"Content-Type": "application/json"
		}
		
		try:
			response = requests.get(url, params=params, headers=headers)
			response.raise_for_status()
			
			# If response is PDF content, we should return it or save it
			# We'll return the raw content and let the caller handle it (e.g. attach to doc)
			return {
				"success": True,
				"content": response.content,
				"content_type": response.headers.get("Content-Type", "application/pdf")
			}
		except Exception as e:
			frappe.log_error(f"Delhivery Packing Slip Failed: {str(e)}", "Delhivery Integration")
			return {"success": False, "error": str(e)}

	def cancel_shipment(self, awb):
		url = f"{self.base_url}/api/p/edit"
		headers = {
			"Authorization": f"Token {self.api_token}",
			"Content-Type": "application/json"
		}
		data = {
			"waybill": awb,
			"cancellation": "true"
		}
		try:
			response = requests.post(url, json=data, headers=headers)
			return response.json()
		except Exception as e:
			frappe.log_error(f"Delhivery Cancellation Failed: {str(e)}", "Delhivery Integration")
			return {"status": "Failed", "error": str(e)}
