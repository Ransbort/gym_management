// Gym Requests table on Patient Encounter (custom field added by
// gym_management.integrations.healthcare.setup_custom_fields).
frappe.ui.form.on("Patient Encounter", {
	onload_post_render(frm) {
		const field = frm.get_field("custom_gym_prescription");
		if (!field) return;
		field.grid.editable_fields = [
			{ fieldname: "request_type", columns: 2 },
			{ fieldname: "membership_plan", columns: 3 },
			{ fieldname: "pt_package", columns: 3 },
			{ fieldname: "priority", columns: 2 },
		];
		field.grid.refresh();
	},
});

frappe.ui.form.on("Gym Prescription", {
	request_type(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.request_type === "Membership") frappe.model.set_value(cdt, cdn, "pt_package", null);
		else frappe.model.set_value(cdt, cdn, "membership_plan", null);
	},
});
