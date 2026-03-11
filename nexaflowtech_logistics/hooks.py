app_name = "nexaflowtech_logistics"
app_title = "Nexaflowtech Logistics"
app_publisher = "Nexaflow"
app_description = "App for Delhivery B2C shipment integration"
app_email = "nexaflowtech007@gmail.com"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/nexaflowtech_logistics/css/nexaflowtech_logistics.css"
# app_include_js = "/assets/nexaflowtech_logistics/js/nexaflowtech_logistics.js"

# include js, css files in header of web template
# web_include_css = "/assets/nexaflowtech_logistics/css/nexaflowtech_logistics.css"
# web_include_js = "/assets/nexaflowtech_logistics/js/nexaflowtech_logistics.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nexaflowtech_logistics/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Delivery Note": "public/js/delivery_note.js",
	"Sales Order": "public/js/sales_order.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "nexaflowtech_logistics/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "nexaflowtech_logistics.utils.jinja_methods",
#	"filters": "nexaflowtech_logistics.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "nexaflowtech_logistics.install.before_install"
# after_install = "nexaflowtech_logistics.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "nexaflowtech_logistics.uninstall.before_uninstall"
# after_uninstall = "nexaflowtech_logistics.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "nexaflowtech_logistics.utils.before_app_install"
# after_app_install = "nexaflowtech_logistics.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "nexaflowtech_logistics.utils.before_app_uninstall"
# after_app_uninstall = "nexaflowtech_logistics.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nexaflowtech_logistics.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Order": {
		"on_submit": "nexaflowtech_logistics.events.sales_order.on_submit",
		"on_cancel": "nexaflowtech_logistics.events.sales_order.on_cancel"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"nexaflowtech_logistics.background_jobs.update_tracking_status"
	],
}

# Testing
# -------

# before_tests = "nexaflowtech_logistics.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "nexaflowtech_logistics.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "nexaflowtech_logistics.task.get_dashboard_data"
# }

# request_hooks = {
#	"frappe.app.next_hook": "nexaflowtech_logistics.utils.next_hook"
# }

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["name", "in", [
                "Sales Order-custom_awb_number",
                "Sales Order-custom_courier_name",
                "Sales Order-custom_shipment_status",
                "Delivery Note-custom_awb_number",
                "Delivery Note-custom_courier_name",
                "Delivery Note-custom_shipment_status"
            ]]
        ]
    }
]
