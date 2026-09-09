// Copyright (c) 2026, Ransford Borketey and contributors
// For license information, please see license.txt
//
// Desk "Trainer" page - the Desk-side equivalent of the website Trainer
// dashboard (www/gym-portal/trainer.*). A Gym Trainer signs into the Desk
// and works from here instead of the website portal; Gym Staff/Gym
// Manager/System Manager get a Trainer picker so they can look at (and
// check members in/out for) any trainer, not just their own.

frappe.pages['trainer'].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Trainer'),
		single_column: true,
	});

	new GymTrainerPage(page);
};

class GymTrainerPage {
	constructor(page) {
		this.page = page;
		this.selected_trainer = null;

		this.$wrapper = $(`
			<div class="gtp-wrapper" style="padding: 0 5px;">
				<div class="gtp-toolbar" style="display:flex; align-items:center; gap: 12px; margin-bottom: 15px; flex-wrap: wrap;"></div>
				<div class="gtp-empty text-muted" style="display:none; padding: 30px 0;"></div>
				<div class="gtp-body" style="display:none;">
					<h4>${__('My Class Schedule')}</h4>
					<div class="gtp-classes"></div>

					<h4 style="margin-top: 25px;">${__('Upcoming PT Sessions')}</h4>
					<div class="gtp-pt-sessions"></div>

					<h4 style="margin-top: 25px;">${__('My Members')}</h4>
					<div class="gtp-members"></div>
				</div>
			</div>
		`).appendTo(this.page.body);

		this.refresh();
	}

	call(method, args) {
		return frappe.call({
			method: `gym_management.gym_management.page.trainer.trainer.${method}`,
			args: args || {},
		});
	}

	refresh() {
		this.call('get_dashboard', { trainer: this.selected_trainer }).then((r) => {
			this.data = r.message || {};
			this.render_toolbar();
			if (!this.data.trainer) {
				this.$wrapper.find('.gtp-body').hide();
				this.$wrapper.find('.gtp-empty').text(
					__('No Trainer profile is linked to your account. Ask a manager to link it under Trainer > User.')
				).show();
				return;
			}
			this.$wrapper.find('.gtp-empty').hide();
			this.$wrapper.find('.gtp-body').show();
			this.render_classes();
			this.render_pt_sessions();
			this.render_members();
		});
	}

	render_toolbar() {
		const $toolbar = this.$wrapper.find('.gtp-toolbar').empty();
		const t = this.data.trainer;

		if (t) {
			$(`<div><strong>${frappe.utils.escape_html(t.trainer_name)}</strong>
				<span class="text-muted">&nbsp;&mdash;&nbsp;${frappe.utils.escape_html(t.status || '')}</span></div>`)
				.appendTo($toolbar);
		}

		if (this.data.can_pick) {
			const $select = $('<select class="form-control" style="width: 220px;"></select>').appendTo($toolbar);
			$select.append(`<option value="">${__('Select a trainer...')}</option>`);
			this.call('get_trainers').then((r) => {
				(r.message || []).forEach((row) => {
					const opt = $(`<option value="${row.name}">${frappe.utils.escape_html(row.trainer_name)}</option>`);
					if (t && row.name === t.name) opt.prop('selected', true);
					$select.append(opt);
				});
			});
			$select.on('change', () => {
				this.selected_trainer = $select.val() || null;
				this.refresh();
			});
		}
	}

	render_classes() {
		const $el = this.$wrapper.find('.gtp-classes').empty();
		const rows = this.data.classes || [];
		if (!rows.length) {
			$el.append(`<div class="text-muted">${__('No classes assigned to you.')}</div>`);
			return;
		}
		const $table = $(`<table class="table table-bordered"><thead><tr>
			<th>${__('Class')}</th><th>${__('Day')}</th><th>${__('Time')}</th><th>${__('Room')}</th><th>${__('Capacity')}</th>
		</tr></thead><tbody></tbody></table>`).appendTo($el);
		const $tbody = $table.find('tbody');
		rows.forEach((c) => {
			$tbody.append(`<tr>
				<td>${frappe.utils.escape_html(c.class_type || '')}</td>
				<td>${frappe.utils.escape_html(c.day_of_week || '')}</td>
				<td>${frappe.utils.escape_html(c.start_time || '')} - ${frappe.utils.escape_html(c.end_time || '')}</td>
				<td>${frappe.utils.escape_html(c.room || '-')}</td>
				<td>${c.capacity != null ? c.capacity : '-'}</td>
			</tr>`);
		});
	}

	render_pt_sessions() {
		const $el = this.$wrapper.find('.gtp-pt-sessions').empty();
		const rows = this.data.pt_sessions || [];
		if (!rows.length) {
			$el.append(`<div class="text-muted">${__('No upcoming PT sessions.')}</div>`);
			return;
		}
		const $table = $(`<table class="table table-bordered"><thead><tr>
			<th>${__('Member')}</th><th>${__('Date')}</th><th>${__('Time')}</th><th>${__('Duration')}</th>
		</tr></thead><tbody></tbody></table>`).appendTo($el);
		const $tbody = $table.find('tbody');
		rows.forEach((s) => {
			$tbody.append(`<tr>
				<td><a href="/app/gym-member/${encodeURIComponent(s.member)}">${frappe.utils.escape_html(s.member)}</a></td>
				<td>${frappe.utils.escape_html(s.session_date || '')}</td>
				<td>${frappe.utils.escape_html(s.start_time || '-')}</td>
				<td>${s.duration_minutes || '-'} min</td>
			</tr>`);
		});
	}

	render_members() {
		const $el = this.$wrapper.find('.gtp-members').empty();
		const rows = this.data.members || [];
		const checked_in = new Set(this.data.checked_in_members || []);
		if (!rows.length) {
			$el.append(`<div class="text-muted">${__('No members assigned to you yet.')}</div>`);
			return;
		}
		const $table = $(`<table class="table table-bordered"><thead><tr>
			<th>${__('Member')}</th><th>${__('Status')}</th><th>${__('Phone')}</th><th></th>
		</tr></thead><tbody></tbody></table>`).appendTo($el);
		const $tbody = $table.find('tbody');
		rows.forEach((m) => {
			const is_in = checked_in.has(m.name);
			const $tr = $(`<tr>
				<td><a href="/app/gym-member/${encodeURIComponent(m.name)}">${frappe.utils.escape_html(m.member_name)}</a></td>
				<td>${frappe.utils.escape_html(m.membership_status || '')}</td>
				<td>${frappe.utils.escape_html(m.phone || '-')}</td>
				<td></td>
			</tr>`);
			const $btn = $(
				`<button class="btn btn-xs ${is_in ? 'btn-default' : 'btn-primary'}">${is_in ? __('Check Out') : __('Check In')}</button>`
			);
			$btn.on('click', () => {
				$btn.prop('disabled', true);
				this.call(is_in ? 'check_out' : 'check_in', { member: m.name })
					.then(() => {
						frappe.show_alert({ message: is_in ? __('Checked out.') : __('Checked in.'), indicator: 'green' });
						this.refresh();
					})
					.catch(() => {
						$btn.prop('disabled', false);
					});
			});
			$tr.find('td').last().append($btn);
			$tbody.append($tr);
		});
	}
}
