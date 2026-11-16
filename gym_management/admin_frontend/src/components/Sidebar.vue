<template>
  <aside class="flex h-full w-16 shrink-0 flex-col items-center border-r border-slate-200 bg-white py-3">
    <nav class="flex flex-1 flex-col items-center gap-1">
      <router-link
        v-for="item in items" :key="item.name" :to="item.to"
        :data-tooltip="item.label"
        class="group relative flex h-11 w-11 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-900 after:pointer-events-none after:absolute after:left-full after:top-1/2 after:z-50 after:ml-2.5 after:-translate-y-1/2 after:whitespace-nowrap after:rounded-md after:bg-gray-900 after:px-2.5 after:py-1.5 after:text-xs after:font-semibold after:text-white after:opacity-0 after:shadow-lg after:transition-opacity after:content-[attr(data-tooltip)] hover:after:opacity-100"
        active-class="!bg-[var(--gym-accent-tint)] !text-[var(--gym-accent)]"
      >
        <i :class="['bi', item.icon, 'text-lg']"></i>
        <span
          v-if="item.name === 'Requests' && requestCount"
          class="absolute right-1 top-1 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white"
        >{{ requestCount > 99 ? '99+' : requestCount }}</span>
      </router-link>
    </nav>

    <!-- Gym Settings popup (GymSettingsModal.vue) - starts with just Theme
         Color; the full Desk form (/app/gym-settings) still exists for
         everything not yet moved in here. Sign out already lives in
         TopBar's user dropdown, so this bottom slot is free for the
         setting staff reach for most: branding, security, defaults. -->
    <button
      type="button"
      data-tooltip="Gym Settings"
      class="group relative mb-1 flex h-11 w-11 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-900 after:pointer-events-none after:absolute after:left-full after:top-1/2 after:z-50 after:ml-2.5 after:-translate-y-1/2 after:whitespace-nowrap after:rounded-md after:bg-gray-900 after:px-2.5 after:py-1.5 after:text-xs after:font-semibold after:text-white after:opacity-0 after:shadow-lg after:transition-opacity after:content-[attr(data-tooltip)] hover:after:opacity-100"
      @click="showSettings = true"
    >
      <i class="bi bi-gear text-lg"></i>
    </button>

    <GymSettingsModal v-if="showSettings" @close="showSettings = false" />
  </aside>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import GymSettingsModal from '@/components/GymSettingsModal.vue';
import { call } from '@/api/frappe';
import { initSocket } from '@/socket';

const showSettings = ref(false);

// Badge on the Requests icon: doctor-issued gym requests still waiting to
// be accepted (see healthcare_requests.py). Refreshed live on the same
// realtime event Requests.vue listens to.
const requestCount = ref(0);
async function loadRequestCount() {
  try {
    requestCount.value = (await call('gym_management.healthcare_requests.get_gym_request_count')) || 0;
  } catch (e) {
    requestCount.value = 0;
  }
}
onMounted(() => {
  loadRequestCount();
  initSocket().on('gym_request_update', loadRequestCount);
});
onUnmounted(() => {
  initSocket().off('gym_request_update', loadRequestCount);
});

const items = [
  { name: 'Overview', to: '/', icon: 'bi-speedometer2', label: 'Overview' },
  { name: 'CheckIn', to: '/checkin', icon: 'bi-door-open', label: 'Check-In' },
  { name: 'Members', to: '/members', icon: 'bi-people', label: 'Members' },
  { name: 'Memberships', to: '/memberships', icon: 'bi-credit-card', label: 'Memberships' },
  { name: 'PersonalTraining', to: '/personal-training', icon: 'bi-stopwatch', label: 'Personal Training' },
  { name: 'Requests', to: '/requests', icon: 'bi-clipboard2-pulse', label: 'Doctor Requests' },
];
</script>
