"""
Test script for the Notes API
Run this after starting the backend server
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_create_note():
    """Test creating a note"""
    print("\n1️⃣ Testing CREATE note...")
    data = {
        "title": "Test Note",
        "content": "This is a test note created by the test script.",
        "category": "Testing",
        "tags": "test, api, demo"
    }
    response = requests.post(f"{BASE_URL}/notes", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        note = response.json()
        print(f"✅ Created note ID: {note['id']}")
        return note['id']
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_get_all_notes():
    """Test getting all notes"""
    print("\n2️⃣ Testing GET all notes...")
    response = requests.get(f"{BASE_URL}/notes")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        notes = response.json()
        print(f"✅ Found {len(notes)} notes")
        for note in notes:
            print(f"   - [{note['id']}] {note['title']} ({note['category']})")
    else:
        print(f"❌ Error: {response.text}")

def test_get_note(note_id):
    """Test getting a specific note"""
    print(f"\n3️⃣ Testing GET note {note_id}...")
    response = requests.get(f"{BASE_URL}/notes/{note_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        note = response.json()
        print(f"✅ Retrieved note: {note['title']}")
        print(f"   Content: {note['content'][:50]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_update_note(note_id):
    """Test updating a note"""
    print(f"\n4️⃣ Testing UPDATE note {note_id}...")
    data = {
        "title": "Updated Test Note",
        "content": "This note has been updated!"
    }
    response = requests.put(f"{BASE_URL}/notes/{note_id}", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        note = response.json()
        print(f"✅ Updated note: {note['title']}")
    else:
        print(f"❌ Error: {response.text}")

def test_search_notes():
    """Test searching notes"""
    print("\n5️⃣ Testing SEARCH notes...")
    response = requests.get(f"{BASE_URL}/notes?search=test")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        notes = response.json()
        print(f"✅ Found {len(notes)} notes matching 'test'")
    else:
        print(f"❌ Error: {response.text}")

def test_get_categories():
    """Test getting categories"""
    print("\n6️⃣ Testing GET categories...")
    response = requests.get(f"{BASE_URL}/notes-categories")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        categories = response.json()
        print(f"✅ Categories: {', '.join(categories)}")
    else:
        print(f"❌ Error: {response.text}")

def test_export_notes():
    """Test exporting notes"""
    print("\n7️⃣ Testing EXPORT notes...")
    response = requests.get(f"{BASE_URL}/notes-export")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Export successful ({len(response.content)} bytes)")
        print("First 200 characters:")
        print(response.text[:200])
    else:
        print(f"❌ Error: {response.text}")

def test_delete_note(note_id):
    """Test deleting a note"""
    print(f"\n8️⃣ Testing DELETE note {note_id}...")
    response = requests.delete(f"{BASE_URL}/notes/{note_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 204:
        print(f"✅ Deleted note {note_id}")
    else:
        print(f"❌ Error: {response.text}")

def main():
    print("="*60)
    print("🧪 NOTES API TEST SUITE")
    print("="*60)
    print("Make sure the backend server is running on http://localhost:8000")
    
    try:
        # Test creating a note
        note_id = test_create_note()
        
        if note_id:
            # Test other operations
            test_get_all_notes()
            test_get_note(note_id)
            test_update_note(note_id)
            test_search_notes()
            test_get_categories()
            test_export_notes()
            
            # Clean up - delete the test note
            test_delete_note(note_id)
        
        print("\n" + "="*60)
        print("✅ TEST SUITE COMPLETED")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to the backend server")
        print("Please make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
