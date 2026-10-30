import { getSeverityColor, getSeverityIcon, getSeverityLabel, getStats } from './severity';

describe('severity labels', () => {
  test('maps each band to its label', () => {
    expect(getSeverityLabel(10)).toBe('CRITICAL');
    expect(getSeverityLabel(8)).toBe('CRITICAL');
    expect(getSeverityLabel(7)).toBe('HIGH');
    expect(getSeverityLabel(6)).toBe('HIGH');
    expect(getSeverityLabel(5)).toBe('MEDIUM');
    expect(getSeverityLabel(4)).toBe('MEDIUM');
    expect(getSeverityLabel(3)).toBe('LOW');
    expect(getSeverityLabel(0)).toBe('LOW');
  });

  test('the boundaries are inclusive at the bottom of each band', () => {
    expect(getSeverityLabel(7.9)).toBe('HIGH');
    expect(getSeverityLabel(8.0)).toBe('CRITICAL');
  });

  test('a missing or broken severity does not throw', () => {
    expect(getSeverityLabel(undefined)).toBe('LOW');
    expect(getSeverityLabel(null)).toBe('LOW');
    expect(getSeverityLabel('nonsense')).toBe('LOW');
  });

  test('colour and icon agree with the label', () => {
    expect(getSeverityColor(9)).toBe('#ef4444');
    expect(getSeverityIcon(9)).toBe('🚨');
    expect(getSeverityColor(1)).toBe('#10b981');
  });
});

describe('getStats', () => {
  test('counts each band', () => {
    const alerts = [{ severity: 9 }, { severity: 7 }, { severity: 5 }, { severity: 1 }];
    expect(getStats(alerts)).toEqual({ total: 4, critical: 1, high: 1, medium: 1, low: 1 });
  });

  test('the bands always add up to the total', () => {
    const alerts = [{ severity: 9 }, { severity: 7 }, { severity: 7 }, { severity: 2 }];
    const { total, critical, high, medium, low } = getStats(alerts);
    expect(critical + high + medium + low).toBe(total);
  });

  test('no alerts gives zeroes rather than NaN', () => {
    expect(getStats([])).toEqual({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
    expect(getStats()).toEqual({ total: 0, critical: 0, high: 0, medium: 0, low: 0 });
  });
});
