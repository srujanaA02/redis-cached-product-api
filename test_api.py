"""
Quick API Test Script
Tests all CRUD operations and cache behavior
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check():
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_create_product():
    print_section("2. Create Product")
    product_data = {
        "name": "API Test Product",
        "description": "Testing product creation",
        "price": 99.99,
        "stock_quantity": 50
    }
    response = requests.post(f"{BASE_URL}/products", json=product_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()["id"] if response.status_code == 201 else None


def test_get_product(product_id, attempt=1):
    print_section(f"3.{attempt}. Get Product (Attempt {attempt})")
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    if attempt == 1:
        print("\n⚡ Expected: Cache MISS (first request)")
    else:
        print("\n🚀 Expected: Cache HIT (from Redis)")
    return response.status_code == 200


def test_update_product(product_id):
    print_section("4. Update Product")
    update_data = {
        "price": 79.99,
        "stock_quantity": 30
    }
    response = requests.put(f"{BASE_URL}/products/{product_id}", json=update_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("\n🔄 Cache invalidated after update")
    return response.status_code == 200


def test_delete_product(product_id):
    print_section("5. Delete Product")
    response = requests.delete(f"{BASE_URL}/products/{product_id}")
    print(f"Status: {response.status_code}")
    print("\n🗑️  Cache invalidated after deletion")
    return response.status_code == 204


def test_get_deleted_product(product_id):
    print_section("6. Try to Get Deleted Product")
    response = requests.get(f"{BASE_URL}/products/{product_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("\n✅ Correctly returns 404 for deleted product")
    return response.status_code == 404


def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  High-Performance Product API - Integration Test          ║")
    print("║  Testing Cache-Aside Pattern & Cache Invalidation         ║")
    print("╚════════════════════════════════════════════════════════════╝")

    results = []

    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))

    # Test 2: Create Product
    product_id = test_create_product()
    if not product_id:
        print("\n❌ Failed to create product. Stopping tests.")
        return

    results.append(("Create Product", True))

    # Test 3: Get Product (Cache Miss)
    time.sleep(1)
    results.append(("Get Product (Cache Miss)", test_get_product(product_id, 1)))

    # Test 4: Get Product Again (Cache Hit)
    time.sleep(1)
    results.append(("Get Product (Cache Hit)", test_get_product(product_id, 2)))

    # Test 5: Update Product
    time.sleep(1)
    results.append(("Update Product", test_update_product(product_id)))

    # Test 6: Get Updated Product (Cache Miss after invalidation)
    time.sleep(1)
    results.append(("Get After Update", test_get_product(product_id, 3)))

    # Test 7: Delete Product
    time.sleep(1)
    results.append(("Delete Product", test_delete_product(product_id)))

    # Test 8: Get Deleted Product (404)
    time.sleep(1)
    results.append(("Get Deleted (404)", test_get_deleted_product(product_id)))

    # Summary
    print_section("Test Results Summary")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
