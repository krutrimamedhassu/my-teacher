#!/usr/bin/env python3
"""
Test script for streaming chat functionality.
This script demonstrates both SSE and WebSocket streaming endpoints.
"""

import asyncio
import aiohttp
import json
import websockets
import time
from typing import AsyncGenerator


async def test_sse_streaming():
    """Test Server-Sent Events streaming endpoint."""
    print("=== Testing SSE Streaming ===")
    
    url = "http://localhost:8000/api/v1/streaming/chat"
    payload = {
        "input": "Explain quantum physics in simple terms",
        "conversation_id": "test-conversation-123",
        "model": "gpt-4o"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            print(f"Status: {response.status}")
            
            if response.status == 200:
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            print(f"SSE Event: {data}")
                        except json.JSONDecodeError:
                            print(f"Raw SSE line: {line_str}")
            else:
                print(f"Error: {response.status}")
                text = await response.text()
                print(f"Response: {text}")


async def test_simple_sse_streaming():
    """Test simple SSE streaming endpoint without conversation context."""
    print("\n=== Testing Simple SSE Streaming ===")
    
    url = "http://localhost:8000/api/v1/streaming/chat/simple"
    payload = {
        "input": "What is the capital of France?",
        "model": "gpt-4o"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            print(f"Status: {response.status}")
            
            if response.status == 200:
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            print(f"SSE Event: {data}")
                        except json.JSONDecodeError:
                            print(f"Raw SSE line: {line_str}")
            else:
                print(f"Error: {response.status}")
                text = await response.text()
                print(f"Response: {text}")


async def test_websocket_streaming():
    """Test WebSocket streaming endpoint."""
    print("\n=== Testing WebSocket Streaming ===")
    
    uri = "ws://localhost:8000/api/v1/websocket/ws/test-client-123"
    
    async with websockets.connect(uri) as websocket:
        print("WebSocket connected")
        
        # Send a chat message
        message = {
            "type": "chat",
            "input": "Tell me a short joke",
            "model": "gpt-4o"
        }
        
        await websocket.send(json.dumps(message))
        print(f"Sent message: {message}")
        
        # Receive streaming response
        response_text = ""
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                print(f"WebSocket Event: {data}")
                
                if data.get("type") == "content":
                    response_text += data.get("content", "")
                elif data.get("type") == "complete":
                    print(f"Complete response: {data.get('response', '')}")
                    break
                elif data.get("type") == "error":
                    print(f"Error: {data.get('message', '')}")
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break


async def test_conversation_websocket():
    """Test conversation-specific WebSocket endpoint."""
    print("\n=== Testing Conversation WebSocket ===")
    
    conversation_id = "test-conversation-456"
    uri = f"ws://localhost:8000/api/v1/websocket/ws/chat/{conversation_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"WebSocket connected for conversation: {conversation_id}")
        
        # Send a chat message
        message = {
            "type": "chat",
            "input": "What is machine learning?",
            "model": "gpt-4o"
        }
        
        await websocket.send(json.dumps(message))
        print(f"Sent message: {message}")
        
        # Receive streaming response
        response_text = ""
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)
                print(f"WebSocket Event: {data}")
                
                if data.get("type") == "content":
                    response_text += data.get("content", "")
                elif data.get("type") == "complete":
                    print(f"Complete response: {data.get('response', '')}")
                    break
                elif data.get("type") == "error":
                    print(f"Error: {data.get('message', '')}")
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break


async def test_ping_pong():
    """Test WebSocket ping/pong for connection health."""
    print("\n=== Testing WebSocket Ping/Pong ===")
    
    uri = "ws://localhost:8000/api/v1/websocket/ws/test-client-ping"
    
    async with websockets.connect(uri) as websocket:
        print("WebSocket connected for ping test")
        
        # Send ping
        ping_message = {"type": "ping"}
        await websocket.send(json.dumps(ping_message))
        print("Sent ping")
        
        # Expect pong
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"Received: {data}")
            
            if data.get("type") == "pong":
                print("Ping/pong successful!")
            else:
                print("Unexpected response type")
                
        except asyncio.TimeoutError:
            print("Timeout waiting for pong")
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Run all streaming tests."""
    print("Starting streaming API tests...")
    print("Make sure the FastAPI server is running on localhost:8000")
    print()
    
    try:
        # Test SSE streaming
        await test_sse_streaming()
        
        # Test simple SSE streaming
        await test_simple_sse_streaming()
        
        # Test WebSocket streaming
        await test_websocket_streaming()
        
        # Test conversation WebSocket
        await test_conversation_websocket()
        
        # Test ping/pong
        await test_ping_pong()
        
        print("\n=== All tests completed ===")
        
    except Exception as e:
        print(f"Error running tests: {e}")
        print("Make sure the server is running and the endpoints are available")


if __name__ == "__main__":
    asyncio.run(main()) 