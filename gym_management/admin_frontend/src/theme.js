// Applies Gym Settings' configurable Theme Color as a handful of CSS custom
// properties on <html>, which every component then references via Tailwind
// arbitrary-value classes (e.g. `bg-[var(--gym-accent)]`) instead of a
// hardcoded `indigo-600` - see admin_frontend/README.md's "Theming" note.
//
// Plain CSS custom properties rather than extending tailwind.config.js's
// color palette: Tailwind's palette is resolved at build time, but the
// accent color is per-site data that only exists at runtime (fetched from
// Gym Settings), so there's nothing for a build-time config to point at.
//
// Only one color is ever stored (Gym Settings.theme_color); the hover/tint/
// ring variants below are derived from it here so the rest of the app never
// has to think about shade math.
function hexToRgb(hex) {
  let h = (hex || '').replace('#', '').trim();
  if (h.length === 3) h = h.split('').map((c) => c + c).join('');
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return { r: 79, g: 70, b: 229 }; // fallback: #4f46e5
  const num = parseInt(h, 16);
  return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
}

function mix(a, b, amount) {
  return {
    r: Math.round(a.r + (b.r - a.r) * amount),
    g: Math.round(a.g + (b.g - a.g) * amount),
    b: Math.round(a.b + (b.b - a.b) * amount),
  };
}

function rgbStr({ r, g, b }) {
  return `rgb(${r} ${g} ${b})`;
}

export function applyTheme(hex) {
  const base = hexToRgb(hex);
  const black = { r: 0, g: 0, b: 0 };
  const white = { r: 255, g: 255, b: 255 };
  const hover = mix(base, black, 0.12); // ~indigo-600 -> indigo-700
  const tint = mix(base, white, 0.93); // ~indigo-600 -> indigo-50
  const root = document.documentElement.style;
  root.setProperty('--gym-accent', rgbStr(base));
  root.setProperty('--gym-accent-hover', rgbStr(hover));
  root.setProperty('--gym-accent-tint', rgbStr(tint));
  root.setProperty('--gym-accent-ring', `rgb(${base.r} ${base.g} ${base.b} / 0.25)`);
}
