import React, {useEffect, useState} from 'react';

function App(){
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        // Use collector service name inside Docker, but allow override for local dev
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiUrl}/api/alerts`);

        if(res.ok){
          const data = await res.json();
          setAlerts(data);
          setError(null);
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

  return (
    <div style={{padding:20, fontFamily:'Segoe UI, Roboto, sans-serif'}}>
      <h2>SIEM Playground — Alerts</h2>
      {loading && <div>Loading alerts...</div>}
      {error && <div style={{color:'red'}}>Error: {error}</div>}
      <div>
        {!loading && alerts.length === 0 && <div>No alerts yet. Replay demo telemetry to see detection.</div>}
        {alerts.map((a,i) => (
          <div key={i} style={{border:'1px solid #ddd', padding:10, margin:8, borderRadius:6}}>
            <strong>{a.name}</strong> — severity: {a.severity}
            <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(a.enriched, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App;