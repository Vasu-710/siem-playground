# 🛡️ SIEM Playground

![Python Tests](https://github.com/Vasu-710/siem-playground/actions/workflows/python-tests.yml/badge.svg)
![UI Workflow](https://github.com/Vasu-710/siem-playground/actions/workflows/ui-workflow.yml/badge.svg)
[![codecov](https://codecov.io/gh/Vasu-710/siem-playground/branch/main/graph/badge.svg)](https://codecov.io/gh/Vasu-710/siem-playground)

**A lightweight, containerized Security Information and Event Management (SIEM) system for learning, testing, and demonstrating security event correlation and threat intelligence enrichment.**

---

## 🎯 What is SIEM Playground?

SIEM Playground is a full-stack security demo project that simulates an enterprise SIEM environment. It allows you to:

- **Ingest** security telemetry from various sources
- **Normalize** logs into a common schema
- **Correlate** events using custom detection rules
- **Enrich** alerts with threat intelligence
- **Visualize** security alerts in real-time via a React dashboard

Perfect for security engineers, SOC analysts, students, and anyone interested in understanding how modern SIEM systems work.

---

## 🎥 Demo Video

**Coming Soon!**

A full walkthrough video demonstrating:
- Setting up the SIEM Playground
- Ingesting security events
- Viewing real-time alerts
- Creating custom correlation rules

Stay tuned! 🎬

---

## ✨ Features

- 🐳 **Fully Dockerized** - Spin up the entire stack with one command
- 🔍 **Event Correlation** - Built-in rules to detect suspicious patterns
- 🌐 **Threat Enrichment** - Automatic IOC (Indicator of Compromise) lookup
- 📊 **Real-time Dashboard** - React UI to monitor alerts as they happen
- 🧪 **Demo Data Included** - Replay phishing campaign scenarios
- 🔧 **Extensible** - Easy to add custom rules and enrichment sources
- 📈 **CI/CD Ready** - GitHub Actions for testing and coverage

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Collector  │ ───> │   Pipeline   │ ───> │  Alerts DB  │
│  (FastAPI)  │      │ (Correlator) │      │   (/tmp)    │
└─────────────┘      └──────────────┘      └─────────────┘
                             │                      │
                             ↓                      ↓
                     ┌──────────────┐      ┌─────────────┐
                     │  Normalizer  │      │   React UI  │
                     │  & Enricher  │      │ (Dashboard) │
                     └──────────────┘      └─────────────┘
```

**Components:**
- **Collector API** - FastAPI service that ingests events via REST endpoint
- **Pipeline** - Python scripts for normalization, correlation, and enrichment
- **PostgreSQL** - Database for persistent storage (future enhancement)
- **React UI** - Frontend dashboard displaying alerts
- **Replay Tool** - Simulate security events from JSON datasets


---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- Python 3.11+ (for running replay scripts)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Vasu-710/siem-playground.git
cd siem-playground
```

2. **Start the stack:**
```bash
docker-compose up --build
```

This will start:
- PostgreSQL (port 5432)
- Collector API (port 8000)
- Pipeline (background processing)
- React UI (port 3000)

3. **Wait ~15 seconds** for all services to initialize

4. **Access the UI:**
Open your browser to [http://localhost:3000](http://localhost:3000)

5. **Generate demo alerts:**
```bash
python3 tools/replay_to_collector.py
```

You should now see alerts appearing in the dashboard! 🎉

---

## 📚 Usage

### Ingesting Custom Events

Send events to the collector API:

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-11-09T12:00:00Z",
    "source": "firewall",
    "event_type": "connection_blocked",
    "payload": {
      "ip": "192.168.1.100",
      "port": 445,
      "reason": "malicious_ip"
    }
  }'
```

### Viewing Alerts

**Via UI:** [http://localhost:3000](http://localhost:3000)

**Via API:**
```bash
curl http://localhost:8000/api/alerts
```

### Checking Health

```bash
curl http://localhost:8000/health
```

---

## 🔧 Configuration

### Adding Custom Correlation Rules

Edit `pipeline/correlator.py` and add your rule function:

```python
def rule_brute_force(recent_events):
    failed_logins = [e for e in recent_events if e['type'] == 'auth_failed']
    if len(failed_logins) >= 5:
        return {
            "name": "Brute Force Detected",
            "severity": 8,
            "evidence": failed_logins
        }
    return None
```

### Adding Threat Intelligence

Update `pipeline/enricher.py`:

```python
THREAT_DB = {
    "evil.com": {"score": 95, "source": "custom-intel", "tags": ["malware"]},
    "10.0.0.1": {"score": 80, "source": "internal-blacklist", "tags": ["c2"]}
}
```

---

## 🧪 Testing

### Run Python Tests
```bash
docker-compose run --rm pipeline pytest tests/
```

### Run UI Tests
```bash
cd ui
npm test
```

### Coverage Report
```bash
coverage run -m pytest tests/
coverage report
```

---

## 📁 Project Structure

```
siem-playground/
├── collectors/
│   └── api_collector/          # FastAPI ingestion service
│       ├── app/
│       │   └── main.py         # API endpoints
│       └── requirements.txt
├── pipeline/
│   ├── correlator.py           # Event correlation engine
│   ├── normalizer.py           # Log normalization
│   ├── enricher.py             # Threat intel enrichment
│   └── requirements.txt
├── ui/
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   └── index.js            # React entry point
│   ├── public/
│   │   └── index.html
│   └── package.json
├── datasets/
│   └── demo_campaign_replay.json  # Sample phishing events
├── tools/
│   └── replay_to_collector.py     # Event replay script
├── infra/
│   ├── Dockerfile.api
│   └── Dockerfile.ui
├── tests/
│   └── test_parsers.py
├── docker-compose.yml
└── README.md
```

---

## 🛠️ Development

### Logs & Debugging

**View all logs:**
```bash
docker-compose logs -f
```

**View specific service:**
```bash
docker-compose logs -f collector
docker-compose logs -f pipeline
docker-compose logs -f ui
```

**Access container shell:**
```bash
docker exec -it siem-playground-collector-1 bash
```

**Check temp files:**
```bash
docker exec siem-playground-pipeline-1 cat /tmp/siem_events.jsonl
docker exec siem-playground-pipeline-1 cat /tmp/siem_alerts.jsonl
```

### Rebuilding

```bash
# Stop everything
docker-compose down

# Remove volumes (fresh start)
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

---

## 🎓 Learning Resources

This project demonstrates:
- **Event-driven architecture** for security monitoring
- **Log normalization** techniques
- **Correlation rules** for threat detection
- **Threat intelligence integration**
- **Microservices** with Docker
- **REST API design** with FastAPI
- **Real-time dashboards** with React

---

## 🚧 Roadmap

- [ ] Add more correlation rules (brute force, lateral movement, etc.)
- [ ] Integrate real threat intelligence APIs (VirusTotal, AbuseIPDB)
- [ ] Persistent storage with PostgreSQL
- [ ] Authentication & multi-tenancy
- [ ] Export alerts to SIEM formats (CEF, LEEF)
- [ ] Kibana-style query interface
- [ ] Machine learning anomaly detection

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/awesome-rule`)
3. Commit your changes (`git commit -am 'Add awesome correlation rule'`)
4. Push to the branch (`git push origin feature/awesome-rule`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available under the MIT License.

---

## 🙏 Acknowledgments

Built for learning and demonstration purposes. Inspired by enterprise SIEM solutions like Splunk, ELK Stack, and QRadar.

---

## 📧 Contact

**Author:** Vasu Saini  
**GitHub:** [@Vasu-710](https://github.com/Vasu-710)

---

**⭐ If you find this project useful, please consider giving it a star!**