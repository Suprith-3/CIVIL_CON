import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class LoadTester:
    def __init__(self, url, users=50):
        self.url = url
        self.users = users
        self.results = []
        self.start_time = 0

    def make_request(self, user_id):
        try:
            start = time.time()
            # Testing the home page for general load
            response = requests.get(self.url, timeout=10)
            latency = (time.time() - start) * 1000
            self.results.append({
                'user': user_id,
                'status': response.status_code,
                'latency': latency
            })
        except Exception as e:
            self.results.append({'user': user_id, 'status': 'ERROR', 'error': str(e)})

    def run_test(self):
        print(f"🚀 Starting Stress Test: {self.url}")
        print(f"👥 Simulating {self.users} concurrent users...")
        
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.users) as executor:
            executor.map(self.make_request, range(self.users))
            
        self.end_time = time.time()
        self.print_report()

    def print_report(self):
        total_time = self.end_time - self.start_time
        success = [r for r in self.results if r.get('status') == 200]
        errors = [r for r in self.results if r.get('status') == 'ERROR' or r.get('status') != 200]
        
        latencies = [r['latency'] for r in success]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        print("\n" + "="*50)
        print("📊 STRESS TEST REPORT")
        print("="*50)
        print(f"Total Requests: {self.users}")
        print(f"Total Time:     {total_time:.2f}s")
        print(f"Successful:     {len(success)}")
        print(f"Failed/Errors:  {len(errors)}")
        if success:
            print(f"Avg Latency:    {avg_latency:.2f}ms")
            print(f"Min Latency:    {min(latencies):.2f}ms")
            print(f"Max Latency:    {max(latencies):.2f}ms")
        print("="*50)
        
        if len(errors) > 0:
            print("\n❌ SERVER IS STRUGGLING: Some requests failed.")
        elif avg_latency > 2000:
            print("\n⚠️ SERVER IS SLOW: Average latency exceeds 2 seconds.")
        else:
            print("\n✅ SERVER IS STABLE: Handled the load successfully.")

if __name__ == "__main__":
    # TARGET URL
    TARGET = "https://civilconnect-m3lr.onrender.com"
    
    # Start with a safe 50 users to see how the server responds
    tester = LoadTester(TARGET, users=50)
    tester.run_test()
