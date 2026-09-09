<template>
  <div class="mx-auto max-w-4xl px-6 py-10">
    <p v-if="loading" class="text-slate-500">Loading...</p>

    <template v-else-if="data">
      <h1 class="text-2xl font-extrabold text-slate-900">Welcome, {{ data.member.member_name }}</h1>
      <p class="mt-1 text-sm text-slate-500">Membership status: <strong>{{ data.member.membership_status }}</strong></p>

      <p v-if="flash" :class="['mt-4 rounded-lg px-3 py-2 text-sm', flashError ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700']">
        {{ flash }}
      </p>

      <Section title="My Memberships">
        <Table :rows="data.memberships" :columns="['Plan', 'Start', 'End', 'Status', 'Total']" empty="No memberships yet.">
          <tr v-for="m in data.memberships" :key="m.name">
            <td class="py-2 pr-4">{{ m.membership_plan }}</td>
            <td class="py-2 pr-4">{{ m.start_date }}</td>
            <td class="py-2 pr-4">{{ m.end_date }}</td>
            <td class="py-2 pr-4">{{ m.status }}</td>
            <td class="py-2 pr-4">{{ m.grand_total }}</td>
          </tr>
        </Table>
      </Section>

      <Section title="Recent Attendance">
        <Table :rows="data.attendance" :columns="['Check In', 'Check Out', 'Duration (min)']" empty="No attendance recorded yet.">
          <tr v-for="a in data.attendance" :key="a.name">
            <td class="py-2 pr-4">{{ a.check_in_time }}</td>
            <td class="py-2 pr-4">{{ a.check_out_time || '-' }}</td>
            <td class="py-2 pr-4">{{ a.duration_minutes ?? '-' }}</td>
          </tr>
        </Table>
      </Section>

      <Section v-if="data.member.customer" title="Invoices">
        <Table :rows="data.invoices" :columns="['Invoice', 'Date', 'Total', 'Outstanding', 'Status']" empty="No invoices yet.">
          <tr v-for="inv in data.invoices" :key="inv.name">
            <td class="py-2 pr-4">{{ inv.name }}</td>
            <td class="py-2 pr-4">{{ inv.posting_date }}</td>
            <td class="py-2 pr-4">{{ inv.grand_total }}</td>
            <td class="py-2 pr-4">{{ inv.outstanding_amount }}</td>
            <td class="py-2 pr-4">{{ inv.status }}</td>
          </tr>
        </Table>
      </Section>

      <Section title="My Class Bookings">
        <Table :rows="data.my_bookings" :columns="['Class', 'Date', 'Status', '']" empty="No upcoming bookings.">
          <tr v-for="b in data.my_bookings" :key="b.name">
            <td class="py-2 pr-4">{{ b.class_schedule }}</td>
            <td class="py-2 pr-4">{{ b.class_date }}</td>
            <td class="py-2 pr-4">{{ b.status }}</td>
            <td class="py-2 pr-4">
              <button class="gp-btn-sm" :disabled="busy" @click="cancelBooking(b.name)">Cancel</button>
            </td>
          </tr>
        </Table>
      </Section>

      <Section title="Book a Class">
        <Table :rows="data.upcoming_classes" :columns="['Class', 'Trainer', 'Day', 'Time', 'Room', '']" empty="No classes scheduled.">
          <tr v-for="c in data.upcoming_classes" :key="c.name">
            <td class="py-2 pr-4">{{ c.class_type }}</td>
            <td class="py-2 pr-4">{{ c.trainer }}</td>
            <td class="py-2 pr-4">{{ c.day_of_week }}</td>
            <td class="py-2 pr-4">{{ c.start_time }} - {{ c.end_time }}</td>
            <td class="py-2 pr-4">{{ c.room || '-' }}</td>
            <td class="py-2 pr-4">
              <button class="gp-btn-sm-primary" :disabled="busy" @click="bookClass(c.name)">Book</button>
            </td>
          </tr>
        </Table>
      </Section>

      <Section title="My PT Packages">
        <Table
          :rows="data.my_pt_purchases"
          :columns="['Package', 'Status', 'Sessions Used', 'Sessions Remaining', 'Expires']"
          empty="No PT packages yet."
        >
          <tr v-for="p in data.my_pt_purchases" :key="p.name">
            <td class="py-2 pr-4">{{ p.pt_package }}</td>
            <td class="py-2 pr-4">{{ p.status }}</td>
            <td class="py-2 pr-4">{{ p.sessions_used }}</td>
            <td class="py-2 pr-4">{{ p.sessions_remaining }}</td>
            <td class="py-2 pr-4">{{ p.expiry_date || '-' }}</td>
          </tr>
        </Table>
      </Section>

      <Section title="Request a PT Package">
        <p class="mb-3 text-sm text-slate-500">Requesting a package sends it to gym staff to confirm and invoice - it does not take payment.</p>
        <Table :rows="data.pt_packages" :columns="['Package', 'Sessions', 'Validity (days)', 'Price', '']" empty="No PT packages configured yet.">
          <tr v-for="p in data.pt_packages" :key="p.name">
            <td class="py-2 pr-4">{{ p.package_name }}</td>
            <td class="py-2 pr-4">{{ p.no_of_sessions }}</td>
            <td class="py-2 pr-4">{{ p.validity_days }}</td>
            <td class="py-2 pr-4">{{ p.price }}</td>
            <td class="py-2 pr-4">
              <button class="gp-btn-sm-primary" :disabled="busy" @click="requestPt(p.name)">Request</button>
            </td>
          </tr>
        </Table>
      </Section>

      <Section v-if="data.workout_plans.length" title="My Workout Plans">
        <Table :rows="data.workout_plans" :columns="['Plan', 'Start', 'End', 'Status']">
          <tr v-for="w in data.workout_plans" :key="w.name">
            <td class="py-2 pr-4">{{ w.workout_plan || w.name }}</td>
            <td class="py-2 pr-4">{{ w.start_date }}</td>
            <td class="py-2 pr-4">{{ w.end_date }}</td>
            <td class="py-2 pr-4">{{ w.status }}</td>
          </tr>
        </Table>
      </Section>

      <Section v-if="data.diet_plans.length" title="My Diet Plans">
        <Table :rows="data.diet_plans" :columns="['Plan', 'Start', 'End', 'Status']">
          <tr v-for="d in data.diet_plans" :key="d.name">
            <td class="py-2 pr-4">{{ d.diet_plan || d.name }}</td>
            <td class="py-2 pr-4">{{ d.start_date }}</td>
            <td class="py-2 pr-4">{{ d.end_date || '-' }}</td>
            <td class="py-2 pr-4">{{ d.status }}</td>
          </tr>
        </Table>
      </Section>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { h } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

const data = ref(null);
const loading = ref(true);
const busy = ref(false);
const flash = ref('');
const flashError = ref(false);

function showFlash(message, isError) {
  flash.value = message;
  flashError.value = !!isError;
}

async function load() {
  loading.value = true;
  try {
    data.value = await call('gym_management.portal.get_member_dashboard');
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not load your membership data.', true);
  } finally {
    loading.value = false;
  }
}

async function bookClass(classSchedule) {
  busy.value = true;
  try {
    const r = await call('gym_management.portal.book_class', { class_schedule: classSchedule });
    showFlash(`Booked (${r.status}). See it under My Class Bookings.`, false);
    await load();
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not book this class.', true);
  } finally {
    busy.value = false;
  }
}

async function cancelBooking(name) {
  busy.value = true;
  try {
    await call('gym_management.portal.cancel_class_booking', { name });
    showFlash('Booking cancelled.', false);
    await load();
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not cancel this booking.', true);
  } finally {
    busy.value = false;
  }
}

async function requestPt(ptPackage) {
  busy.value = true;
  try {
    const r = await call('gym_management.portal.request_pt_package', { pt_package: ptPackage });
    showFlash(`Requested (${r.status}). Gym staff will follow up to confirm.`, false);
    await load();
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not request this package.', true);
  } finally {
    busy.value = false;
  }
}

onMounted(load);

// Small local components kept in this same file (Section/Table) rather
// than separate files - they're only ever used here and on Trainer.vue's
// own copy, and don't carry enough shared logic yet to be worth a
// components/ import for two call sites.
const Section = {
  props: ['title'],
  render() {
    return h('section', { class: 'mt-8' }, [
      h('h2', { class: 'mb-2 text-lg font-bold text-slate-900' }, this.title),
      this.$slots.default(),
    ]);
  },
};

const Table = {
  props: ['rows', 'columns', 'empty'],
  render() {
    if (!this.rows || !this.rows.length) {
      return h('div', { class: 'text-sm text-slate-500' }, this.empty || 'Nothing here yet.');
    }
    return h('div', { class: 'overflow-x-auto rounded-lg border border-slate-200 bg-white' }, [
      h('table', { class: 'w-full text-left text-sm' }, [
        h('thead', { class: 'border-b border-slate-200 bg-slate-50 text-slate-500' }, [
          h('tr', {}, this.columns.map((c) => h('th', { class: 'py-2 pr-4 pl-4 font-semibold' }, c))),
        ]),
        h('tbody', { class: 'px-4 [&>tr]:border-b [&>tr:last-child]:border-0 [&>tr]:border-slate-100 [&_td:first-child]:pl-4' }, this.$slots.default()),
      ]),
    ]);
  },
};
</script>

<style scoped>
.gp-btn-sm {
  border-radius: 0.375rem;
  border: 1px solid #cbd5e1;
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
}
.gp-btn-sm:hover:not(:disabled) {
  background-color: #f8fafc;
}
.gp-btn-sm:disabled {
  opacity: 0.5;
}
.gp-btn-sm-primary {
  border-radius: 0.375rem;
  border: none;
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  background-color: var(--portal-primary, #ea580c);
}
.gp-btn-sm-primary:hover:not(:disabled) {
  background-color: var(--portal-primary-hover, #c2410c);
}
.gp-btn-sm-primary:disabled {
  opacity: 0.5;
}
</style>
