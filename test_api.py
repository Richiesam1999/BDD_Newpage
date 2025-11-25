"""
Simple test script to test the /generate endpoint with a URL
"""
import requests
import json
import sys

API_URL = "http://localhost:8000"
TEST_URL = "https://karunya.edu/"

def test_generate_endpoint():
    """Test the /generate endpoint"""
    print(f"Testing API endpoint: {API_URL}/generate")
    print(f"URL to analyze: {TEST_URL}")
    print("-" * 60)
    
    try:
        print("Sending POST request...")
        response = requests.post(
            f"{API_URL}/generate",
            json={"url": TEST_URL},
            timeout=600  # 10 minutes timeout for long-running analysis
        )
        
        print(f"Status Code: {response.status_code}")
        print("-" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            print(f"Filename: {result.get('filename')}")
            print(f"Feature Content Length: {len(result.get('feature_content', ''))} characters")
            print("-" * 60)
            print("\nFeature File Content Preview (first 500 chars):")
            print(result.get('feature_content', '')[:500])
            print("\n" + "-" * 60)
            
            # Save to file
            if result.get('feature_content'):
                filename = result.get('filename', 'output.feature')
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result.get('feature_content'))
                print(f"\n✅ Feature file saved as: {filename}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to API server.")
        print(f"   Make sure the server is running at {API_URL}")
        print("   Start it with: uvicorn BDD_Tests.api.main:app --reload")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out. The analysis is taking too long.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    test_generate_endpoint()

