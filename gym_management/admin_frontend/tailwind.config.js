import frappeUIPreset from 'frappe-ui/tailwind';

// frappe-ui's Vue components style themselves with Tailwind utility
// classes that only exist if this app's own Tailwind build sees them, so
// its source has to be in `content` alongside our own - same as POSNext's
// tailwind.config.js.
//
// No custom color tokens here - every color used across this app is a
// stock Tailwind class (indigo-600/700 for the accent, gray-900 for the
// header/sidebar chrome, slate-* for the light content area), so nothing
// needs extending.
export default {
	presets: [frappeUIPreset],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
	],
	plugins: [],
};
