import requests
import time
from datetime import datetime

class PerformanceTestSuite:
    def __init__(self, base_url):
        self.base_url = base_url
        self.results = []
    
    def test_page_load_time(self, endpoint, iterations=3):
        print(f"\n📊 Testing Page Load Time: {endpoint}")
        load_times = []
        
        for i in range(iterations):
            start = time.time()
            response = requests.get(f"{self.base_url}{endpoint}")
            end = time.time()
            
            load_time = (end - start) * 1000
            load_times.append(load_time)
            print(f"  Iteration {i+1}: {load_time:.2f}ms - Status: {response.status_code}")
        
        avg_time = sum(load_times) / len(load_times)
        print(f"  ✓ Average: {avg_time:.2f}ms")
        
        self.results.append({
            'test': 'Page Load Time',
            'endpoint': endpoint,
            'avg_time_ms': avg_time,
            'status': 'PASS' if avg_time < 3000 else 'FAIL'
        })
        return avg_time

    def test_api_health(self):
        print(f"\n📊 Testing API Health Check")
        start = time.time()
        response = requests.get(f"{self.base_url}/health")
        ttfb = (time.time() - start) * 1000
        print(f"  TTFB: {ttfb:.2f}ms - Status: {response.status_code}")
        self.results.append({
            'test': 'API TTFB',
            'ttfb_ms': ttfb,
            'status': 'PASS' if ttfb < 1000 else 'FAIL'
        })

    def generate_report(self):
        print("\n" + "="*60)
        print("🎯 PERFORMANCE TEST REPORT")
        print("="*60)
        for r in self.results:
            status = '✅' if r['status'] == 'PASS' else '❌'
            print(f"{status} {r['test']}: {r}")

if __name__ == '__main__':
    # Use localhost or live URL
    URL = 'https://civilconnect-m3lr.onrender.com'
    tester = PerformanceTestSuite(URL)
    tester.test_page_load_time('/')
    tester.test_api_health()
    tester.generate_report()
