// Severity thresholds, kept out of the component so they can be tested on
// their own and so the dashboard and any future view agree on what HIGH means.

export const LEVELS = [
  { min: 8, label: 'CRITICAL', color: '#ef4444', icon: '🚨' },
  { min: 6, label: 'HIGH', color: '#f59e0b', icon: '⚠️' },
  { min: 4, label: 'MEDIUM', color: '#eab308', icon: '⚡' },
  { min: 0, label: 'LOW', color: '#10b981', icon: '✅' },
];

function levelFor(severity) {
  const value = Number(severity);
  const score = Number.isFinite(value) ? value : 0;
  return LEVELS.find((level) => score >= level.min) || LEVELS[LEVELS.length - 1];
}

export const getSeverityColor = (severity) => levelFor(severity).color;
export const getSeverityLabel = (severity) => levelFor(severity).label;
export const getSeverityIcon = (severity) => levelFor(severity).icon;

// One pass over the alerts rather than four filters, and every alert lands in
// exactly one bucket so the counts always add up to the total.
export function getStats(alerts = []) {
  const stats = { total: alerts.length, critical: 0, high: 0, medium: 0, low: 0 };
  alerts.forEach((alert) => {
    stats[getSeverityLabel(alert && alert.severity).toLowerCase()] += 1;
  });
  return stats;
}
