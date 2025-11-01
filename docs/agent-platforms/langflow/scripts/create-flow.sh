#!/bin/bash
# Create Coffee Roasting Agent Flow in LangFlow via API

set -e

LANGFLOW_URL=${LANGFLOW_URL:-"http://localhost:7860"}
LANGFLOW_API_KEY=${LANGFLOW_API_KEY:-""}

echo "🚀 Creating Coffee Roasting Agent in LangFlow"
echo "============================================="
echo ""

if [ -z "$LANGFLOW_API_KEY" ]; then
    echo "⚠️  LANGFLOW_API_KEY not set"
    echo ""
    echo "📋 Steps to get your API key:"
    echo "   1. Open LangFlow UI: $LANGFLOW_URL"
    echo "   2. Click your profile/avatar in top-right"
    echo "   3. Go to 'Settings' → 'API Keys'"
    echo "   4. Click 'Create new secret key'"
    echo "   5. Copy the key and set it:"
    echo ""
    echo "      export LANGFLOW_API_KEY='your-api-key-here'"
    echo ""
    echo "   Then run this script again."
    exit 1
fi

echo "✅ API Key found"
echo "📍 LangFlow URL: $LANGFLOW_URL"
echo ""

# Create a minimal flow using the Simple Agent template as base
# We'll start with Basic Prompting template and add tools via API

echo "🔨 Creating flow..."

FLOW_JSON=$(cat <<'EOF'
{
  "name": "Coffee Roasting Agent",
  "description": "First crack detection agent with MCP integration",
  "data": {
    "nodes": [
      {
        "id": "ChatInput-1",
        "type": "ChatInput",
        "position": {"x": 100, "y": 200},
        "data": {
          "node": {
            "template": {
              "input_value": {
                "value": ""
              }
            },
            "display_name": "Chat Input"
          }
        }
      },
      {
        "id": "ChatOutput-1",
        "type": "ChatOutput",
        "position": {"x": 700, "y": 200},
        "data": {
          "node": {
            "display_name": "Chat Output"
          }
        }
      },
      {
        "id": "OpenAIModel-1",
        "type": "OpenAIModel",
        "position": {"x": 400, "y": 200},
        "data": {
          "node": {
            "template": {
              "model_name": {
                "value": "gpt-4-turbo-preview"
              },
              "openai_api_key": {
                "value": ""
              },
              "system_message": {
                "value": "You are a coffee roasting assistant. Help users monitor their roasts and detect first crack. When asked to start monitoring, respond with: 'Please use the MCP tools to start detection. Ask me: what audio source would you like to use? (audio_file, usb_microphone, or builtin_microphone)'"
              }
            },
            "display_name": "OpenAI"
          }
        }
      }
    ],
    "edges": [
      {
        "id": "edge-1",
        "source": "ChatInput-1",
        "target": "OpenAIModel-1"
      },
      {
        "id": "edge-2",
        "source": "OpenAIModel-1",
        "target": "ChatOutput-1"
      }
    ]
  }
}
EOF
)

RESPONSE=$(curl -s -X POST \
  "$LANGFLOW_URL/api/v1/flows/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -d "$FLOW_JSON")

echo ""
echo "📝 Response:"
echo "$RESPONSE" | jq '.' || echo "$RESPONSE"
echo ""

FLOW_ID=$(echo "$RESPONSE" | jq -r '.id // .flow_id // empty')

if [ -n "$FLOW_ID" ]; then
    echo "✅ Flow created successfully!"
    echo "   Flow ID: $FLOW_ID"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Open LangFlow UI: $LANGFLOW_URL"
    echo "   2. Find 'Coffee Roasting Agent' in your projects"
    echo "   3. Click to edit and add your OpenAI API key"
    echo "   4. Add custom Python tools for MCP integration"
    echo ""
else
    echo "❌ Failed to create flow"
    echo "   Check the response above for errors"
    exit 1
fi
