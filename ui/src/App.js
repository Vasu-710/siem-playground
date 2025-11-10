import React, { useEffect, useState } from 'react';

function App() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiUrl}/api/alerts`);

        if (res.ok) {
          const data = await res.json();
          setAlerts(data);
          setError(null);
          setLastUpdate(new Date());
        } else {
          setError(`Failed to fetch: ${res.status}`);
        }
      } catch (err) {
        setError(`Error: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const id = setInterval(fetchAlerts, 3000);
    return () => clearInterval(id);
  }, []);

  const getSeverityColor = (severity) => {
    if (severity >= 8) return '#ef4444'; // Red - Critical
    if (severity >= 6) return '#f59e0b'; // Orange - High
    if (severity >= 4) return '#eab308'; // Yellow - Medium
    return '#10b981'; // Green - Low
  };

  const getSeverityLabel = (severity) => {
    if (severity >= 8) return 'CRITICAL';
    if (severity >= 6) return 'HIGH';
    if (severity >= 4) return 'MEDIUM';
    return 'LOW';
  };

  const getSeverityIcon = (severity) => {
    if (severity >= 8) return '🚨';
    if (severity >= 6) return '⚠️';
    if (severity >= 4) return '⚡';
    return '✅';
  };

  const getStats = () => {
    return {
      total: alerts.length,
      critical: alerts.filter(a => a.severity >= 8).length,
      high: alerts.filter(a => a.severity >= 6 && a.severity < 8).length,
      medium: alerts.filter(a => a.severity >= 4 && a.severity < 6).length,
      low: alerts.filter(a => a.severity < 4).length,
    };
  };

  const stats = getStats();

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    }}>
      {/* Header */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto 30px',
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        padding: '30px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '32px', fontWeight: '700', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '12px' }}>
              🛡️ SIEM Playground
            </h1>
            <p style={{ margin: '8px 0 0 0', color: '#6b7280', fontSize: '14px' }}>
              Real-time Security Event Monitoring • Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{
              background: loading ? '#fbbf24' : '#10b981',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              animation: loading ? 'pulse 2s infinite' : 'none'
            }} />
            <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '500' }}>
              {loading ? 'Syncing...' : 'Live'}
            </span>
          </div>
        </div>
      </div>

      {/* Stats Dashboard */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto 30px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px'
      }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
          borderLeft: '4px solid #3b82f6'
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '600' }}>TOTAL ALERTS</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#1f2937' }}>{stats.total}</div>
        </div>

        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
          borderLeft: '4px solid #ef4444'
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '600' }}>🚨 CRITICAL</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#ef4444' }}>{stats.critical}</div>
        </div>

        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
          borderLeft: '4px solid #f59e0b'
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '600' }}>⚠️ HIGH</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#f59e0b' }}>{stats.high}</div>
        </div>

        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
          borderLeft: '4px solid #eab308'
        }}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '600' }}>⚡ MEDIUM</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#eab308' }}>{stats.medium}</div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {error && (
          <div style={{
            background: '#fee2e2',
            border: '1px solid #ef4444',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '20px',
            color: '#991b1b',
            fontWeight: '500'
          }}>
            ⚠️ {error}
          </div>
        )}

        {!loading && alerts.length === 0 && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '16px',
            padding: '60px 40px',
            textAlign: 'center',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
          }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>🔍</div>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '24px', color: '#1f2937' }}>No Alerts Detected</h3>
            <p style={{ margin: 0, color: '#6b7280', fontSize: '16px' }}>
              System is running smoothly. Run the replay script to generate demo alerts.
            </p>
            <code style={{
              display: 'inline-block',
              marginTop: '20px',
              padding: '12px 20px',
              background: '#f3f4f6',
              borderRadius: '8px',
              color: '#374151',
              fontSize: '14px',
              fontFamily: 'monospace'
            }}>
              python3 tools/replay_to_collector.py
            </code>
          </div>
        )}

        {alerts.map((alert, i) => (
          <div key={i} style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '16px',
            padding: '28px',
            marginBottom: '20px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)',
            borderLeft: `6px solid ${getSeverityColor(alert.severity)}`,
            transition: 'transform 0.2s, box-shadow 0.2s'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '28px' }}>{getSeverityIcon(alert.severity)}</span>
                  <h3 style={{ margin: 0, fontSize: '24px', fontWeight: '700', color: '#1f2937' }}>
                    {alert.name}
                  </h3>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '6px 14px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    fontWeight: '700',
                    background: getSeverityColor(alert.severity),
                    color: 'white',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {getSeverityLabel(alert.severity)} • Score: {alert.severity}
                  </span>
                  <span style={{ fontSize: '14px', color: '#9ca3af' }}>
                    Alert #{i + 1}
                  </span>
                </div>
              </div>
            </div>

            {alert.enriched && Object.keys(alert.enriched).length > 0 && (
              <div style={{
                background: '#f9fafb',
                borderRadius: '12px',
                padding: '20px',
                border: '1px solid #e5e7eb'
              }}>
                <div style={{ fontSize: '14px', fontWeight: '700', color: '#374151', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  🔬 THREAT INTELLIGENCE
                </div>
                <pre style={{
                  margin: 0,
                  fontSize: '13px',
                  color: '#1f2937',
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  fontFamily: "'Fira Code', 'Courier New', monospace",
                  lineHeight: '1.6'
                }}>
                  {JSON.stringify(alert.enriched, null, 2)}
                </pre>
              </div>
            )}

            {alert.evidence && (
              <details style={{ marginTop: '16px' }}>
                <summary style={{
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#6b7280',
                  padding: '8px 0',
                  userSelect: 'none'
                }}>
                  📋 View Evidence
                </summary>
                <div style={{
                  background: '#f9fafb',
                  borderRadius: '8px',
                  padding: '16px',
                  marginTop: '8px',
                  border: '1px solid #e5e7eb'
                }}>
                  <pre style={{
                    margin: 0,
                    fontSize: '12px',
                    color: '#4b5563',
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                    fontFamily: 'monospace',
                    lineHeight: '1.5'
                  }}>
                    {JSON.stringify(alert.evidence, null, 2)}
                  </pre>
                </div>
              </details>
            )}
          </div>
        ))}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}

export default App;