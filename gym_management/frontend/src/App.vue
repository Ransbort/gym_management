<template>
  <div class="flex h-screen flex-col overflow-hidden bg-slate-50">
    <Navbar />
    <main class="min-h-0 flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Navbar from '@/components/Navbar.vue';
</script>
