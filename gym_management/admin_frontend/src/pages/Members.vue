<template>
  <div class="flex h-full flex-col gap-4 overflow-hidden bg-slate-50 p-6 lg:flex-row">
    <!-- List + filters -->
    <section class="flex min-w-0 flex-1 flex-col">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 class="text-xl font-bold text-slate-900">Members</h1>
        <button
          class="rounded-lg bg-[var(--gym-accent)] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[var(--gym-accent-hover)]"
          @click="showCreateMember = true"
        >
          <i class="bi bi-person-plus"></i> New Member
        </button>
      </div>

      <div class="mb-3 flex gap-2">
        <input v-model="listQuery" type="text" placeholder="Search members by name, phone or email..." class="w-full max-w-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @input="debouncedList" />
        <select v-model="listStatus" class="w-44 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[var(--gym-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--gym-accent-ring)]" @change="loadList">
          <option value="">All statuses</option>
          <option v-for="s in ['Active', 'Expired', 'Suspended', 'Cancelled', 'No Membership']" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        <p v-if="listLoading" class="px-4 py-6 text-sm text-slate-500">Loading...</p>
        <p v-else-if="!members.length" class="px-4 py-6 text-sm text-slate-500">No members found.</p>
        <table v-else class="w-full text-left text-sm">
          <thead class="sticky top-0 border-b border-slate-200 bg-white text-slate-500">
            <tr>
              <th class="px-4 py-2 font-semibold">Name</th>
              <th class="px-4 py-2 font-semibold">Phone</th>
              <th class="px-4 py-2 font-semibold">Gender</th>
              <th class="px-4 py-2 font-semibold">Joined</th>
              <th class="px-4 py-2 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in members" :key="m.name"
              class="cursor-pointer border-b border-slate-100 border-l-4 border-l-transparent text-slate-700 hover:bg-slate-50"
              :class="{ '!border-l-[var(--gym-accent)] !bg-[var(--gym-accent-tint)]': selected && selected.member.name === m.name }"
              @click="selectMember(m.name)">
              <td class="px-4 py-2">
                <div class="flex items-center gap-2">
                  <img v-if="m.photo || m.user_image" :src="m.photo || m.user_image" alt="" class="h-6 w-6 shrink-0 rounded-full object-cover" />
                  <span v-else class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--gym-accent-tint)] text-[10px] font-bold text-[var(--gym-accent)]">{{ memberInitials(m.member_name) }}</span>
                  {{ m.member_name }}
                </div>
              </td>
              <td class="px-4 py-2">{{ m.phone || '-' }}</td>
              <td class="px-4 py-2">{{ m.gender || '-' }}</td>
              <td class="px-4 py-2">{{ m.date_joined || '-' }}</td>
              <td class="px-4 py-2">
                <span
                  class="rounded-full px-2 py-0.5 text-xs font-semibold"
                  :class="m.membership_status === 'Active' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'"
                >{{ m.membership_status || 'Unknown' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Detail -->
    <section class="flex w-full flex-col lg:w-96 lg:shrink-0">
      <div v-if="!selected" class="flex h-full items-center justify-center rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
        Select a member to view their details and membership history.
      </div>
      <div v-else class="flex h-full flex-col overflow-y-auto rounded-xl border border-slate-200 bg-white p-4">
        <div class="flex flex-col items-center text-center">
          <img v-if="selected.member.photo || selected.member.user_image" :src="selected.member.photo || selected.member.user_image" alt="" class="h-20 w-20 shrink-0 rounded-full object-cover" />
          <span v-else class="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-[var(--gym-accent-tint)] text-xl font-bold text-[var(--gym-accent)]">{{ memberInitials(selected.member.member_name) }}</span>
          <div class="mt-2 min-w-0">
            <h2 class="truncate text-sm font-semibold text-slate-900">{{ selected.member.member_name }}</h2>
            <p class="truncate text-xs text-slate-500">{{ selected.member.name }}</p>
          </div>
        </div>

        <dl class="mt-3 grid grid-cols-2 gap-2 text-xs">
          <dt class="text-slate-500">Phone</dt><dd class="text-right text-slate-700">{{ selected.member.phone || '-' }}</dd>
          <dt class="text-slate-500">Email</dt><dd class="truncate text-right text-slate-700">{{ selected.member.email || '-' }}</dd>
          <dt class="text-slate-500">Gender</dt><dd class="text-right text-slate-700">{{ selected.member.gender || '-' }}</dd>
          <dt class="text-slate-500">Date of Birth</dt><dd class="text-right text-slate-700">{{ selected.member.date_of_birth || '-' }}</dd>
          <dt class="text-slate-500">Date Joined</dt><dd class="text-right text-slate-700">{{ selected.member.date_joined || '-' }}</dd>
          <dt class="text-slate-500">Status</dt><dd class="text-right font-semibold text-slate-700">{{ selected.member.membership_status || 'Unknown' }}</dd>
        </dl>

        <div v-if="selected.member.address" class="mt-3 border-t border-slate-100 pt-3">
          <h3 class="mb-1 text-xs font-semibold text-slate-600">Address</h3>
          <p class="text-xs text-slate-600">{{ selected.member.address }}</p>
        </div>

        <div v-if="selected.member.emergency_contact_name || selected.member.emergency_contact_phone" class="mt-3 border-t border-slate-100 pt-3">
          <h3 class="mb-1 text-xs font-semibold text-slate-600">Emergency Contact</h3>
          <p class="text-xs text-slate-600">{{ selected.member.emergency_contact_name || '-' }} &middot; {{ selected.member.emergency_contact_phone || '-' }}</p>
        </div>

        <div v-if="selected.member.health_notes" class="mt-3 border-t border-slate-100 pt-3">
          <h3 class="mb-1 text-xs font-semibold text-slate-600">Health Notes</h3>
          <p class="text-xs text-slate-600">{{ selected.member.health_notes }}</p>
        </div>

        <div class="mt-4 border-t border-slate-200 pt-3">
          <h3 class="mb-2 text-xs font-semibold text-slate-600">Membership History</h3>
          <p v-if="!selected.memberships.length" class="text-xs text-slate-500">No memberships yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="m in selected.memberships" :key="m.name" class="flex items-center justify-between gap-2 text-slate-600">
              <span class="truncate">{{ m.membership_plan }} &middot; {{ m.start_date }}</span>
              <span class="shrink-0 font-semibold" :class="m.outstanding_amount > 0 ? 'text-amber-600' : 'text-emerald-600'">{{ m.status }}</span>
            </li>
          </ul>
        </div>

        <!-- Fitness & Nutrition - mirrors the same-named dashboard group on
             Gym Member's own Desk form (generate.py's dashboard_links), so
             staff can add/view these without leaving the dashboard. -->
        <div class="mt-4 border-t border-slate-200 pt-3">
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-600">Body Measurements</h3>
            <button type="button" class="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200" title="Add Body Measurement" @click="showAddMeasurement = true">
              <i class="bi bi-plus text-sm"></i>
            </button>
          </div>
          <p v-if="!selected.body_measurements.length" class="text-xs text-slate-500">No measurements recorded yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="bm in selected.body_measurements" :key="bm.name" class="flex items-center justify-between gap-2 text-slate-600">
              <span class="truncate">{{ bm.measurement_date }} &middot; {{ bm.weight_kg }}kg &middot; BMI {{ bm.bmi || '-' }}</span>
              <span class="shrink-0 font-semibold text-slate-500">{{ bm.weight_status || '-' }}</span>
            </li>
          </ul>
        </div>

        <div class="mt-4 border-t border-slate-200 pt-3">
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-600">Assigned Workout Plans</h3>
            <button type="button" class="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200" title="Assign Workout Plan" @click="showAssignWorkout = true">
              <i class="bi bi-plus text-sm"></i>
            </button>
          </div>
          <p v-if="!selected.assigned_workout_plans.length" class="text-xs text-slate-500">No workout plans assigned yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="wp in selected.assigned_workout_plans" :key="wp.name" class="flex items-center justify-between gap-2 text-slate-600">
              <span class="truncate">{{ wp.workout_plan || 'Custom plan' }} &middot; {{ wp.start_date }}</span>
              <span class="shrink-0 font-semibold" :class="wp.status === 'Active' ? 'text-emerald-600' : 'text-slate-400'">{{ wp.status }}</span>
            </li>
          </ul>
        </div>

        <div class="mt-4 border-t border-slate-200 pt-3">
          <div class="mb-2 flex items-center justify-between">
            <h3 class="text-xs font-semibold text-slate-600">Assigned Diet Plans</h3>
            <button type="button" class="flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200" title="Assign Diet Plan" @click="showAssignDiet = true">
              <i class="bi bi-plus text-sm"></i>
            </button>
          </div>
          <p v-if="!selected.assigned_diet_plans.length" class="text-xs text-slate-500">No diet plans assigned yet.</p>
          <ul v-else class="space-y-1.5 text-xs">
            <li v-for="dp in selected.assigned_diet_plans" :key="dp.name" class="flex items-center justify-between gap-2 text-slate-600">
              <span class="truncate">{{ dp.diet_plan || 'Custom plan' }} &middot; {{ dp.start_date }}</span>
              <span class="shrink-0 font-semibold" :class="dp.status === 'Active' ? 'text-emerald-600' : 'text-slate-400'">{{ dp.status }}</span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <CreateMemberModal
      v-if="showCreateMember"
      @close="showCreateMember = false"
      @created="onMemberCreated"
    />

    <AddBodyMeasurementModal
      v-if="showAddMeasurement"
      :member="selected.member.name"
      @close="showAddMeasurement = false"
      @created="onMeasurementCreated"
    />

    <AssignWorkoutPlanModal
      v-if="showAssignWorkout"
      :member="selected.member.name"
      @close="showAssignWorkout = false"
      @created="onWorkoutPlanAssigned"
    />

    <AssignDietPlanModal
      v-if="showAssignDiet"
      :member="selected.member.name"
      @close="showAssignDiet = false"
      @created="onDietPlanAssigned"
    />
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { call, firstServerMessage } from '@/api/frappe';
import CreateMemberModal from '@/components/CreateMemberModal.vue';
import AddBodyMeasurementModal from '@/components/AddBodyMeasurementModal.vue';
import AssignWorkoutPlanModal from '@/components/AssignWorkoutPlanModal.vue';
import AssignDietPlanModal from '@/components/AssignDietPlanModal.vue';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

const members = ref([]);
const listQuery = ref('');
const listStatus = ref('');
const listLoading = ref(true);
const selected = ref(null);
const showCreateMember = ref(false);
const showAddMeasurement = ref(false);
const showAssignWorkout = ref(false);
const showAssignDiet = ref(false);
let listTimer = null;

function memberInitials(name) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
}

async function loadList() {
  listLoading.value = true;
  try {
    members.value = await call('gym_management.admin_api.list_members', { query: listQuery.value, status: listStatus.value });
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load members.', 'error');
  } finally {
    listLoading.value = false;
  }
}
function debouncedList() {
  clearTimeout(listTimer);
  listTimer = setTimeout(loadList, 250);
}

async function selectMember(name) {
  try {
    selected.value = await call('gym_management.admin_api.get_member', { name });
  } catch (err) {
    ui.showToast(firstServerMessage(err) || 'Could not load this member.', 'error');
  }
}

function onMemberCreated(member) {
  showCreateMember.value = false;
  ui.showToast(`${member.member_name} created.`);
  loadList();
}

function onMeasurementCreated() {
  showAddMeasurement.value = false;
  ui.showToast('Measurement saved.');
  if (selected.value) selectMember(selected.value.member.name);
}

function onWorkoutPlanAssigned() {
  showAssignWorkout.value = false;
  ui.showToast('Workout plan assigned.');
  if (selected.value) selectMember(selected.value.member.name);
}

function onDietPlanAssigned() {
  showAssignDiet.value = false;
  ui.showToast('Diet plan assigned.');
  if (selected.value) selectMember(selected.value.member.name);
}

onMounted(loadList);
watch(() => ui.refreshKey, () => {
  loadList();
  if (selected.value) selectMember(selected.value.member.name);
});
</script>
