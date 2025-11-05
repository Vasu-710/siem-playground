import React, {useEffect, useState} from 'react';

function App(){
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const fetchAlerts = async () => {
      const res = await fetch('/api/alerts'); // create a tiny server proxy or extend collector to serve alerts
      if(res.ok){
        const data = await res.json();
        setAlerts(data);
      }
    };
    fetchAlerts();
    const id = setInterval(fetchAlerts, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{padding:20, fontFamily:'Segoe UI, Roboto, sans-serif'}}>
      <h2>SIEM Playground — Alerts</h2>
      <div>
        {alerts.length === 0 && <div>No alerts yet. Replay demo telemetry to see detection.</div>}
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
