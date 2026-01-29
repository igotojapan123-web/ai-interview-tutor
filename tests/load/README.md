# Load Testing Guide

## Overview
FlyReady Lab uses Locust for load and performance testing.

## Installation
```bash
pip install locust locust-plugins
```

## Running Tests

### Web UI Mode
```bash
# Start Locust with web interface
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open http://localhost:8089 in browser
```

### Headless Mode
```bash
# Run without UI (for CI/CD)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --csv=results/load_test
```

### Distributed Mode
```bash
# Master node
locust -f tests/load/locustfile.py --master

# Worker nodes
locust -f tests/load/locustfile.py --worker --master-host=<master-ip>
```

## Test Scenarios

### Smoke Test
Quick test to verify system is working:
```bash
locust -f tests/load/locustfile.py --headless -u 5 -r 1 -t 1m
```

### Load Test
Normal load testing:
```bash
locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 10m
```

### Stress Test
Find system limits:
```bash
locust -f tests/load/locustfile.py --headless -u 500 -r 50 -t 15m
```

### Spike Test
Test sudden traffic spikes:
```bash
locust -f tests/load/locustfile.py --headless -u 1000 -r 200 -t 5m
```

### Soak Test
Extended duration test:
```bash
locust -f tests/load/locustfile.py --headless -u 50 -r 5 -t 2h
```

## Metrics

### Key Metrics to Monitor
- **Response Time**: p50, p95, p99 percentiles
- **Throughput**: Requests per second (RPS)
- **Error Rate**: Percentage of failed requests
- **Concurrent Users**: Number of active users

### Target SLAs
| Metric | Target |
|--------|--------|
| p95 Response Time | < 500ms |
| p99 Response Time | < 1000ms |
| Error Rate | < 1% |
| Availability | > 99.9% |

## Results Analysis

### CSV Output
Results are saved to CSV files:
- `results/load_test_stats.csv` - Request statistics
- `results/load_test_failures.csv` - Failed requests
- `results/load_test_stats_history.csv` - Time-series data

### Grafana Dashboard
Import the dashboard from `monitoring/grafana/dashboards/load_test.json`

## Tips

1. **Warm-up**: Start with low users and gradually increase
2. **Realistic Data**: Use varied test data, not same values
3. **Monitor Backend**: Watch CPU, memory, DB connections
4. **Run Multiple Times**: Results can vary between runs
5. **Clean Environment**: Reset state between test runs
