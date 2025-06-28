import requests
import unittest
import json
from datetime import datetime

class AcademicSearchEngineAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AcademicSearchEngineAPITest, self).__init__(*args, **kwargs)
        # Use the public endpoint from the frontend .env file
        self.base_url = "https://0a039bb0-0e16-4586-b8b4-07acf27060f9.preview.emergentagent.com/api"
        self.test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    def test_01_api_root(self):
        """Test the API root endpoint"""
        print("\n🔍 Testing API root endpoint...")
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Academic Search Engine API")
        self.assertEqual(data["version"], "1.0.0")
        print("✅ API root endpoint test passed")

    def test_02_basic_search(self):
        """Test basic search functionality"""
        print("\n🔍 Testing basic search...")
        search_data = {
            "query": "machine learning",
            "limit": 5
        }
        response = requests.post(f"{self.base_url}/search", json=search_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("papers", data)
        self.assertIn("total_count", data)
        self.assertIn("query_info", data)
        
        # Verify query info
        self.assertEqual(data["query_info"]["query"], "machine learning")
        
        # Verify papers structure if any returned
        if len(data["papers"]) > 0:
            paper = data["papers"][0]
            self.assertIn("title", paper)
            self.assertIn("authors", paper)
            self.assertIn("source", paper)
            
        print(f"✅ Basic search test passed - Found {data['total_count']} papers")
        return data["total_count"]

    def test_03_advanced_search(self):
        """Test advanced search with filters"""
        print("\n🔍 Testing advanced search with filters...")
        search_data = {
            "query": "neural networks",
            "author": "Hinton",
            "year_from": 2010,
            "year_to": 2023,
            "limit": 5
        }
        response = requests.post(f"{self.base_url}/search", json=search_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify query info contains filters
        self.assertEqual(data["query_info"]["query"], "neural networks")
        self.assertEqual(data["query_info"]["author"], "Hinton")
        self.assertEqual(data["query_info"]["year_range"], "2010-2023")
        
        # Check if papers match the year filter if any returned
        if len(data["papers"]) > 0:
            for paper in data["papers"]:
                if paper["year"]:
                    self.assertGreaterEqual(paper["year"], 2010)
                    self.assertLessEqual(paper["year"], 2023)
        
        print(f"✅ Advanced search test passed - Found {data['total_count']} papers")

    def test_04_search_history(self):
        """Test search history functionality"""
        print("\n🔍 Testing search history...")
        
        # First, perform a unique search to ensure we have a history entry
        unique_query = f"test query {self.test_timestamp}"
        search_data = {"query": unique_query, "limit": 2}
        search_response = requests.post(f"{self.base_url}/search", json=search_data)
        self.assertEqual(search_response.status_code, 200)
        
        # Now get the search history
        response = requests.get(f"{self.base_url}/search/history")
        self.assertEqual(response.status_code, 200)
        history = response.json()
        
        # Verify history structure
        self.assertIsInstance(history, list)
        if len(history) > 0:
            entry = history[0]
            self.assertIn("id", entry)
            self.assertIn("query", entry)
            self.assertIn("timestamp", entry)
            self.assertIn("result_count", entry)
            
            # Check if our unique query is in the history
            found_query = False
            for item in history:
                if item["query"] == unique_query:
                    found_query = True
                    break
            
            self.assertTrue(found_query, f"Unique query '{unique_query}' not found in search history")
        
        print(f"✅ Search history test passed - Found {len(history)} history entries")
        return len(history)

    def test_05_clear_history(self):
        """Test clearing search history"""
        print("\n🔍 Testing clear search history...")
        
        # First check if we have history
        initial_response = requests.get(f"{self.base_url}/search/history")
        initial_count = len(initial_response.json())
        
        if initial_count == 0:
            # Create a history entry if none exists
            search_data = {"query": f"test clear {self.test_timestamp}", "limit": 2}
            requests.post(f"{self.base_url}/search", json=search_data)
            
        # Clear history
        clear_response = requests.delete(f"{self.base_url}/search/history")
        self.assertEqual(clear_response.status_code, 200)
        data = clear_response.json()
        self.assertIn("message", data)
        self.assertIn("Deleted", data["message"])
        
        # Verify history is cleared
        after_response = requests.get(f"{self.base_url}/search/history")
        after_count = len(after_response.json())
        self.assertEqual(after_count, 0)
        
        print(f"✅ Clear history test passed")

    def test_06_saved_papers(self):
        """Test saved papers endpoint"""
        print("\n🔍 Testing saved papers...")
        
        # First ensure we have some papers saved by doing a search
        search_data = {"query": "artificial intelligence", "limit": 3}
        search_response = requests.post(f"{self.base_url}/search", json=search_data)
        self.assertEqual(search_response.status_code, 200)
        
        # Now get saved papers
        response = requests.get(f"{self.base_url}/papers/saved")
        self.assertEqual(response.status_code, 200)
        papers = response.json()
        
        # Verify papers structure
        self.assertIsInstance(papers, list)
        if len(papers) > 0:
            paper = papers[0]
            self.assertIn("id", paper)
            self.assertIn("title", paper)
            self.assertIn("authors", paper)
            self.assertIn("source", paper)
        
        print(f"✅ Saved papers test passed - Found {len(papers)} saved papers")

    def test_07_error_handling(self):
        """Test error handling with invalid requests"""
        print("\n🔍 Testing error handling...")
        
        # Test with empty query
        search_data = {"query": "", "limit": 5}
        response = requests.post(f"{self.base_url}/search", json=search_data)
        
        # Either it should return an error or empty results
        if response.status_code != 200:
            self.assertGreaterEqual(response.status_code, 400)
            print("✅ Empty query correctly returned error")
        else:
            data = response.json()
            self.assertEqual(data["total_count"], 0)
            print("✅ Empty query correctly returned zero results")
        
        # Test with invalid JSON
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{self.base_url}/search", data="invalid json", headers=headers)
        self.assertGreaterEqual(response.status_code, 400)
        print("✅ Invalid JSON correctly returned error")
        
        # Test with invalid endpoint
        response = requests.get(f"{self.base_url}/nonexistent")
        self.assertEqual(response.status_code, 404)
        print("✅ Invalid endpoint correctly returned 404")

def run_tests():
    """Run all tests and print summary"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(AcademicSearchEngineAPITest('test_01_api_root'))
    test_suite.addTest(AcademicSearchEngineAPITest('test_02_basic_search'))
    test_suite.addTest(AcademicSearchEngineAPITest('test_03_advanced_search'))
    test_suite.addTest(AcademicSearchEngineAPITest('test_04_search_history'))
    test_suite.addTest(AcademicSearchEngineAPITest('test_05_clear_history'))
    test_suite.addTest(AcademicSearchEngineAPITest('test_06_saved_papers'))
    test_suite.addTest(AcademicSearchEngineAPITest('test_07_error_handling'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n📊 Test Summary:")
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return len(result.failures) + len(result.errors)

if __name__ == "__main__":
    exit_code = run_tests()
    exit(exit_code)