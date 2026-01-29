"""
Load Testing with Locust.

Enterprise-grade performance and load testing.

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 5m
"""

import json
import random
import string
import time
from typing import Optional

from locust import HttpUser, TaskSet, between, task, events
from locust.runners import MasterRunner, WorkerRunner


# =============================================================================
# Test Data Generators
# =============================================================================

def random_email() -> str:
    """Generate random email."""
    chars = string.ascii_lowercase + string.digits
    username = ''.join(random.choice(chars) for _ in range(10))
    return f"{username}@test.flyreadylab.com"


def random_password() -> str:
    """Generate random password."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))


def random_name() -> str:
    """Generate random Korean-style name."""
    surnames = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임"]
    given_names = ["민준", "서연", "지우", "수빈", "지민", "예진", "도윤", "하은", "시우", "지아"]
    return random.choice(surnames) + random.choice(given_names)


def random_answer() -> str:
    """Generate random interview answer."""
    answers = [
        "저는 항공 서비스에 대한 열정을 가지고 있습니다. 고객에게 최상의 서비스를 제공하고 싶습니다.",
        "팀워크를 중요시하며, 어려운 상황에서도 침착하게 대처할 수 있습니다.",
        "다양한 고객 서비스 경험을 통해 문제 해결 능력을 키워왔습니다.",
        "글로벌 환경에서 일하는 것에 대한 강한 동기부여가 있습니다.",
    ]
    return random.choice(answers)


# =============================================================================
# API Tasks
# =============================================================================

class APITasks(TaskSet):
    """API endpoint tasks."""

    def on_start(self):
        """Called when a simulated user starts."""
        self.email = random_email()
        self.password = random_password()
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None

    # =========================================================================
    # Authentication Tasks
    # =========================================================================

    @task(1)
    def register(self):
        """Register a new user."""
        with self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "name": random_name(),
            },
            catch_response=True
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                response.success()
            elif response.status_code == 400:
                # Already registered
                response.success()
            else:
                response.failure(f"Registration failed: {response.status_code}")

    @task(5)
    def login(self):
        """Login user."""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "email": self.email,
                "password": self.password,
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # =========================================================================
    # Interview Tasks
    # =========================================================================

    @task(10)
    def get_questions(self):
        """Get interview questions."""
        interview_type = random.choice([
            "self_introduction",
            "motivation",
            "situational",
            "service_mind",
        ])

        with self.client.get(
            f"/api/v1/interview/questions/{interview_type}",
            headers=self._get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get questions failed: {response.status_code}")

    @task(8)
    def start_interview_session(self):
        """Start an interview session."""
        with self.client.post(
            "/api/v1/interview/sessions",
            json={
                "interview_type": "self_introduction",
                "airline_name": "대한항공",
                "num_questions": 5,
            },
            headers=self._get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.session_id = data.get("id")
                response.success()
            else:
                response.failure(f"Start session failed: {response.status_code}")

    @task(15)
    def submit_answer(self):
        """Submit an interview answer."""
        if not self.session_id:
            return

        with self.client.post(
            f"/api/v1/interview/sessions/{self.session_id}/answer",
            json={
                "answer": random_answer(),
                "duration_seconds": random.uniform(30, 90),
            },
            headers=self._get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 404:
                self.session_id = None
                response.success()
            else:
                response.failure(f"Submit answer failed: {response.status_code}")

    # =========================================================================
    # User Tasks
    # =========================================================================

    @task(5)
    def get_profile(self):
        """Get user profile."""
        with self.client.get(
            "/api/v1/users/me",
            headers=self._get_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.success()  # Not authenticated
            else:
                response.failure(f"Get profile failed: {response.status_code}")

    @task(3)
    def get_progress(self):
        """Get learning progress."""
        with self.client.get(
            "/api/v1/users/me/progress",
            headers=self._get_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Get progress failed: {response.status_code}")

    # =========================================================================
    # Job Tasks
    # =========================================================================

    @task(5)
    def get_jobs(self):
        """Get job listings."""
        with self.client.get(
            "/api/v1/jobs",
            params={"limit": 10, "offset": 0},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get jobs failed: {response.status_code}")

    @task(2)
    def search_jobs(self):
        """Search job listings."""
        airlines = ["대한항공", "아시아나", "제주항공", "진에어", "티웨이"]

        with self.client.get(
            "/api/v1/jobs/search",
            params={"airline": random.choice(airlines)},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search jobs failed: {response.status_code}")

    # =========================================================================
    # Mentor Tasks
    # =========================================================================

    @task(3)
    def get_mentors(self):
        """Get mentor listings."""
        with self.client.get(
            "/api/v1/mentors",
            params={"limit": 10},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get mentors failed: {response.status_code}")

    # =========================================================================
    # Health Check
    # =========================================================================

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_headers(self) -> dict:
        """Get request headers with auth token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers


# =============================================================================
# WebSocket Tasks
# =============================================================================

class WebSocketTasks(TaskSet):
    """WebSocket connection tasks."""

    @task
    def websocket_connect(self):
        """Test WebSocket connection."""
        # Note: Locust doesn't natively support WebSocket
        # Use locust-plugins or custom implementation
        pass


# =============================================================================
# User Behavior Profiles
# =============================================================================

class NormalUser(HttpUser):
    """Normal user behavior profile."""
    tasks = [APITasks]
    wait_time = between(1, 5)
    weight = 7  # 70% of users


class PowerUser(HttpUser):
    """Power user behavior profile (more active)."""
    tasks = [APITasks]
    wait_time = between(0.5, 2)
    weight = 2  # 20% of users


class APIBot(HttpUser):
    """API integration/bot behavior profile."""
    tasks = [APITasks]
    wait_time = between(0.1, 0.5)
    weight = 1  # 10% of users


# =============================================================================
# Event Handlers
# =============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("=" * 60)
    print("FlyReady Lab Load Test Started")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("=" * 60)
    print("FlyReady Lab Load Test Completed")
    print("=" * 60)

    # Print summary
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio * 100:.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median Response Time: {stats.total.median_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests/s: {stats.total.current_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called on each request."""
    if exception:
        print(f"Request failed: {name} - {exception}")


# =============================================================================
# Custom Metrics
# =============================================================================

class CustomMetrics:
    """Custom metrics collector for detailed analysis."""

    def __init__(self):
        self.response_times = []
        self.errors = []

    def add_response(self, endpoint: str, response_time: float, success: bool):
        """Add response metric."""
        self.response_times.append({
            "endpoint": endpoint,
            "time": response_time,
            "success": success,
            "timestamp": time.time()
        })

    def get_summary(self) -> dict:
        """Get metrics summary."""
        if not self.response_times:
            return {}

        times = [r["time"] for r in self.response_times]
        return {
            "total_requests": len(self.response_times),
            "successful": sum(1 for r in self.response_times if r["success"]),
            "failed": sum(1 for r in self.response_times if not r["success"]),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
        }


custom_metrics = CustomMetrics()
