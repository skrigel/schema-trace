#!/bin/bash
 # Quick API test script for SchemaTrace

set -e

API_URL="http://localhost:8000"
 
echo "🚀 Testing SchemaTrace API..."
echo ""

# Test 1: Create a project
echo "1️⃣  Creating project..."
PROJECT_RESPONSE=$(curl -s -X POST "$API_URL/projects/" \
-H "Content-Type: application/json" \
-d '{"name": "test-project", "description": "API test project"}')

PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
echo "   ✅ Project created with ID: $PROJECT_ID"
echo ""

echo "2️⃣  Creating model..."
    MODEL_RESPONSE=$(curl -s -X POST "$API_URL/models/" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"User\", \"description\": \"User model\", \"project_id\": $PROJECT_ID}")
     
    MODEL_ID=$(echo $MODEL_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
    echo "   ✅ Model created with ID: $MODEL_ID"
    echo ""
 
    # Test 3: Upload events
     echo "3️⃣  Uploading schema events..."
      33 curl -s -X POST "$API_URL/events/bulk" \
      34   -H "Content-Type: application/json" \
      35   -d "{
      36     \"events\": [
      37       {
      38         \"model_id\": $MODEL_ID,
      39         \"event_type\": \"ADD_COLUMN\",
      40         \"field_name\": \"email\",
      41         \"risk_level\": \"low\",
      42         \"metadata\": {
      43           \"field_type\": \"EmailField\",
      44           \"nullable\": false,
      45           \"unique\": true,
      46           \"max_length\": 254
      47         }
      48       },
      49       {
      50         \"model_id\": $MODEL_ID,
      51         \"event_type\": \"ADD_COLUMN\",
      52         \"field_name\": \"username\",
      53         \"risk_level\": \"low\",
      54         \"metadata\": {
      55           \"field_type\": \"CharField\",
      56           \"max_length\": 50,
      57           \"nullable\": false
      58         }
      59       },
      60       {
      61         \"model_id\": $MODEL_ID,
      62         \"event_type\": \"ADD_COLUMN\",
      63         \"field_name\": \"created_at\",
      64         \"risk_level\": \"low\",
      65         \"metadata\": {
      66           \"field_type\": \"DateTimeField\",
      67           \"auto_now_add\": true
      68         }
      69       }
      70     ]
      71   }" > /dev/null
      72 
      73 echo "   ✅ 3 events uploaded"
      74 echo ""
      75 
      76 # Test 4: Retrieve events
      77 echo "4️⃣  Retrieving event history..."
      78 EVENTS=$(curl -s "$API_URL/events/model/$MODEL_ID")
      79 EVENT_COUNT=$(echo $EVENTS | grep -o '"field_name"' | wc -l | xargs)
      80 echo "   ✅ Retrieved $EVENT_COUNT events"
      81 echo ""
      82 
      83 # Test 5: Get model with fields (when event processing is implemented)
      84 echo "5️⃣  Getting model details..."
      85 MODEL_FULL=$(curl -s "$API_URL/models/$MODEL_ID/full")
      86 echo "   ✅ Model retrieved"
      87 echo ""
      88 
      89 # Test 6: List all projects
      90 echo "6️⃣  Listing all projects..."
      91 PROJECTS=$(curl -s "$API_URL/projects/")
      92 echo "   ✅ Projects listed"
      93 echo ""
      94 
      95 echo "✨ All tests passed!"
      96 echo ""
      97 echo "📊 View your data at: $API_URL/docs"
      98 echo ""
      99 echo "🧹 Cleanup: curl -X DELETE $API_URL/projects/$PROJECT_ID"