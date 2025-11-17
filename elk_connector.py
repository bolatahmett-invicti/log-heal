"""
ELK (Elasticsearch) Integration
Fetches logs from real ELK stack
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json


class ELKConnector:
    """Fetches logs from Elasticsearch"""
    
    def __init__(self, host: str = "localhost", port: int = 9200, 
                 username: str = None, password: str = None):
        """
        Args:
            host: Elasticsearch host
            port: Elasticsearch port
            username: Authentication username
            password: Authentication password
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.es_client = None
    
    def connect(self):
        """Connect to Elasticsearch"""
        try:
            from elasticsearch import Elasticsearch
            
            if self.username and self.password:
                self.es_client = Elasticsearch(
                    [f"http://{self.host}:{self.port}"],
                    basic_auth=(self.username, self.password)
                )
            else:
                self.es_client = Elasticsearch(
                    [f"http://{self.host}:{self.port}"]
                )
            
            # Test connection
            info = self.es_client.info()
            print(f"✓ Connected to Elasticsearch: {info['version']['number']}")
            return True
            
        except Exception as e:
            print(f"✗ Elasticsearch connection error: {e}")
            return False
    
    def fetch_error_logs(self, 
                        index: str = "app-logs**",
                        time_range_minutes: int = 60,
                        severity: List[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch error logs
        
        Args:
            index: Elasticsearch index pattern
            time_range_minutes: Fetch logs from last N minutes
            severity: Log levels (ERROR, CRITICAL, etc.)
            limit: Maximum number of logs
        """
        if not self.es_client:
            raise Exception("Not connected to Elasticsearch. Call connect() first.")
        
        if severity is None:
            severity = ["ERROR", "CRITICAL", "FATAL"]
        
        # Time range
        time_from = datetime.now() - timedelta(minutes=time_range_minutes)
        
        # Build query
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match_phrase": {
                                "level": "ERROR"
                            }
                        }
                    ]
                }
            },
            "size": limit
        }
        
        try:
            response = self.es_client.search(index=index, body=query)

            logs = []
            for hit in response['hits']['hits']:
                logs.append(hit['_source'])
            
            print(f"✓ Fetched {len(logs)} error logs")
            return logs
            
        except Exception as e:
            print(f"✗ Log fetch error: {e}")
            return []
    
    def format_logs_for_analysis(self, logs: List[Dict[str, Any]]) -> str:
        """Format logs for AI analysis"""
        formatted = []
        
        for log in logs:
            formatted.append(json.dumps(log, indent=2, ensure_ascii=False))
        
        return "\n\n---\n\n".join(formatted)
    
    def get_recent_errors(self, minutes: int = 60) -> str:
        """Fetch and format errors from last X minutes"""
        if not self.es_client:
            self.connect()
        
        logs = self.fetch_error_logs(time_range_minutes=minutes)
        return self.format_logs_for_analysis(logs)


class MockELKConnector:
    """Mock ELK connector for testing"""
    
    def connect(self):
        print("✓ Mock ELK connector (test mode)")
        return True
    
    def fetch_error_logs(self, 
                        index: str = "app-logs**",
                        time_range_minutes: int = 60,
                        severity: List[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Returns sample error logs"""
        sample_logs = [
            {
                "timestamp": "2025-11-17T10:30:45.123Z",
                "level": "ERROR",
                "service": "user-service",
                "message": "NullPointerException in UserController",
                "exception": {
                    "class": "java.lang.NullPointerException",
                    "message": "Cannot invoke method on null object",
                    "stacktrace": [
                        "at com.example.UserController.getUser(UserController.java:45)",
                        "at com.example.UserService.findById(UserService.java:23)"
                    ]
                },
                "context": {
                    "file": "src/main/java/com/example/UserController.java",
                    "line": 45,
                    "method": "getUser"
                }
            },
            {
                "timestamp": "2025-11-17T10:35:12.456Z",
                "level": "ERROR",
                "service": "payment-service",
                "message": "Database connection timeout",
                "exception": {
                    "class": "java.sql.SQLException",
                    "message": "Connection timeout after 30s",
                    "stacktrace": [
                        "at com.example.PaymentService.processPayment(PaymentService.java:78)",
                        "at com.example.DatabasePool.getConnection(DatabasePool.java:34)"
                    ]
                },
                "context": {
                    "file": "src/main/java/com/example/PaymentService.java",
                    "line": 78,
                    "method": "processPayment"
                }
            }
        ]
        
        print(f"✓ Mock: {len(sample_logs)} sample logs returned")
        return sample_logs
    
    def get_recent_errors(self, minutes: int = 60) -> str:
        """Returns formatted sample error logs"""
        logs = self.fetch_error_logs(time_range_minutes=minutes)
        return "\n\n---\n\n".join([json.dumps(log, indent=2, ensure_ascii=False) for log in logs])


def create_elk_connector(use_mock: bool = True, **kwargs) -> ELKConnector:
    """
    ELK connector factory
    
    Args:
        use_mock: If True, returns mock connector (for testing)
        **kwargs: Connection parameters for real ELK
    """
    if use_mock:
        return MockELKConnector()
    else:
        return ELKConnector(**kwargs)
