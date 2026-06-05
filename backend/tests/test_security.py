import requests

class SecurityTestSuite:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def test_cors(self):
        print("\n🔐 Testing CORS Policy")
        malicious_origin = 'https://malicious-site.com'
        response = requests.options(
            f"{self.base_url}/api/auth/login",
            headers={'Origin': malicious_origin, 'Access-Control-Request-Method': 'POST'}
        )
        allowed_origin = response.headers.get('Access-Control-Allow-Origin')
        if allowed_origin == malicious_origin or allowed_origin == '*':
            print("  ❌ FAIL: Permissive CORS detected!")
        else:
            print(f"  ✅ PASS: Malicious origin blocked/not allowed. (Header: {allowed_origin})")

    def test_rate_limiting(self):
        print("\n🔐 Testing Rate Limiting (Login)")
        for i in range(7):
            response = requests.post(f"{self.base_url}/api/auth/login", json={'email': 'a@b.com', 'password': 'w'})
            print(f"  Attempt {i+1}: {response.status_code}")
            if response.status_code == 429:
                print("  ✅ PASS: Rate limiting triggered successfully.")
                return
        print("  ❌ FAIL: Rate limiting not triggered after 7 attempts.")

if __name__ == '__main__':
    URL = 'https://civilconnect-m3lr.onrender.com'
    tester = SecurityTestSuite(URL)
    tester.test_cors()
    tester.test_rate_limiting()
