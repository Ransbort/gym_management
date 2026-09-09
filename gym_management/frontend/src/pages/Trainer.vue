<template>
  <div class="mx-auto max-w-4xl px-6 py-10">
    <p v-if="loading" class="text-slate-500">Loading...</p>

    <template v-else-if="data">
      <h1 class="text-2xl font-extrabold text-slate-900">Welcome, {{ data.trainer.trainer_name }}</h1>

      <p v-if="flash" :class="['mt-4 rounded-lg px-3 py-2 text-sm', flashError ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700']">
        {{ flash }}
      </p>

      <Section title="My Class Schedule">
        <Table :rows="data.classes" :columns="['Class', 'Day', 'Time', 'Room', 'Capacity']" empty="No classes assigned to you.">
          <tr v-for="c in data.classes" :key="c.name">
            <td class="py-2 pr-4">{{ c.class_type }}</td>
            <td class="py-2 pr-4">{{ c.day_of_week }}</td>
            <td class="py-2 pr-4">{{ c.start_time }} - {{ c.end_time }}</td>
            <td class="py-2 pr-4">{{ c.room || '-' }}</td>
            <td class="py-2 pr-4">{{ c.capacity }}</td>
          </tr>
        </Table>
      </Section>

      <Section title="Upcoming PT Sessions">
        <Table :rows="data.pt_sessions" :columns="['Member', 'Date', 'Time', 'Duration']" empty="No upcoming PT sessions.">
          <tr v-for="s in data.pt_sessions" :key="s.name">
            <td class="py-2 pr-4">{{ s.member }}</td>
            <td class="py-2 pr-4">{{ s.session_date }}</td>
            <td class="py-2 pr-4">{{ s.start_time || '-' }}</td>
            <td class="py-2 pr-4">{{ s.duration_minutes || '-' }} min</td>
          </tr>
        </Table>
      </Section>

      <Section title="My Members">
        <p class="mb-3 text-sm text-slate-500">Members with an active membership assigned to you, or a workout/diet plan you assigned.</p>
        <Table :rows="data.members" :columns="['Member', 'Status', 'Phone', '']" empty="No members assigned to you yet.">
          <tr v-for="m in data.members" :key="m.name">
            <td class="py-2 pr-4">{{ m.member_name }}</td>
            <td class="py-2 pr-4">{{ m.membership_status }}</td>
            <td class="py-2 pr-4">{{ m.phone || '-' }}</td>
            <td class="py-2 pr-4">
              <button
                v-if="checkedIn.has(m.name)"
                class="gp-btn-sm" :disabled="busy" @click="checkOut(m.name)"
              >Check Out</button>
              <button
                v-else
                class="gp-btn-sm-primary" :disabled="busy" @click="checkIn(m.name)"
              >Check In</button>
            </td>
          </tr>
        </Table>
      </Section>
    </template>
  </div>
</template>

<script setup>
import { computed, h, onMounted, ref } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';

const data = ref(null);
const loading = ref(true);
const busy = ref(false);
const flash = ref('');
const flashError = ref(false);

const checkedIn = computed(() => new Set((data.value && data.value.checked_in_members) || []));

function showFlash(message, isError) {
  flash.value = message;
  flashError.value = !!isError;
}

async function load() {
  loading.value = true;
  try {
    data.value = await call('gym_management.portal.get_trainer_dashboard');
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not load your dashboard.', true);
  } finally {
    loading.value = false;
  }
}

async function checkIn(member) {
  busy.value = true;
  try {
    await call('gym_management.portal.trainer_check_in', { member });
    showFlash('Checked in.', false);
    await load();
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not check this member in.', true);
  } finally {
    busy.value = false;
  }
}

async function checkOut(member) {
  busy.value = true;
  try {
    await call('gym_management.portal.trainer_check_out', { member });
    showFlash('Checked out.', false);
    await load();
  } catch (err) {
    showFlash(firstServerMessage(err) || 'Could not check this member out.', true);
  } finally {
    busy.value = false;
  }
}

onMounted(load);

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
