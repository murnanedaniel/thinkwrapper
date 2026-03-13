// Frontend configuration - loaded from backend /api/config at runtime
// This avoids hardcoding secrets in the frontend build

let _config = null;

export async function loadConfig() {
  if (_config) return _config;
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    if (data.success) {
      _config = data.data;
    } else {
      _config = {};
    }
  } catch {
    _config = {};
  }
  return _config;
}

export function getConfig() {
  return _config || {};
}
