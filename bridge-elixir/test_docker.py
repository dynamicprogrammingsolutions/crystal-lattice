#!/usr/bin/env python3
"""
Integration test for Bridge service Docker deployment.

Tests:
1. Server registration
2. App listing servers
3. Pairing flow
"""

import asyncio
import json
import os
import uuid
import websockets
import sys
from datetime import datetime

BRIDGE_URL = os.environ.get("BRIDGE_URL", "ws://localhost:4000/ws/websocket")
TIMEOUT = 10

ref_counter = 0

def get_ref():
    global ref_counter
    ref_counter += 1
    return str(ref_counter)


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def log(message, color=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if color:
        print(f"{color}[{timestamp}] {message}{Colors.END}")
    else:
        print(f"[{timestamp}] {message}")


def phoenix_message(topic, event, payload):
    """Create a Phoenix-formatted message."""
    return json.dumps({
        "topic": topic,
        "event": event,
        "payload": payload,
        "ref": get_ref()
    })


async def test_server_registration():
    """Test server can register with the bridge."""
    log("🧪 Test 1: Server Registration", Colors.BLUE)
    
    server_id = str(uuid.uuid4())
    
    try:
        async with websockets.connect(f"{BRIDGE_URL}?type=server") as ws:
            log(f"  ✓ Connected as server", Colors.GREEN)
            
            # Join server channel
            join_msg = phoenix_message(f"server:{server_id}", "phx_join", {})
            await ws.send(join_msg)
            
            response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
            log(f"  ← Join response: {json.loads(response)['event']}", Colors.YELLOW)
            
            # Register server
            register_msg = phoenix_message(
                f"server:{server_id}",
                "register",
                {
                    "server_id": server_id,
                    "display_name": "Test Server",
                    "computer_name": "test-computer.local",
                    "location": "Test Lab"
                }
            )
            
            await ws.send(register_msg)
            log(f"  → Sent registration", Colors.YELLOW)
            
            response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
            resp_data = json.loads(response)
            log(f"  ← Received: {resp_data['event']}", Colors.YELLOW)
            
            log(f"✅ Server registration successful\n", Colors.GREEN)
            return True, server_id
            
    except Exception as e:
        log(f"❌ Server registration failed: {e}\n", Colors.RED)
        return False, None


async def test_list_servers():
    """Test app can list registered servers."""
    log("🧪 Test 2: List Servers", Colors.BLUE)
    
    server_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    
    try:
        # First register a server
        server_ws = await websockets.connect(f"{BRIDGE_URL}?type=server")
        
        join_msg = phoenix_message(f"server:{server_id}", "phx_join", {})
        await server_ws.send(join_msg)
        await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
        
        register_msg = phoenix_message(
            f"server:{server_id}",
            "register",
            {
                "server_id": server_id,
                "display_name": "Test Server for Listing",
                "computer_name": "test-list.local",
                "location": "NYC"
            }
        )
        
        await server_ws.send(register_msg)
        await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
        
        log(f"  ✓ Server registered", Colors.GREEN)
        
        # Wait a moment for registration to propagate
        await asyncio.sleep(0.5)
        
        # Now connect as app and list servers
        async with websockets.connect(f"{BRIDGE_URL}?type=app") as app_ws:
            log(f"  ✓ Connected as app", Colors.GREEN)
            
            # Join app channel
            join_msg = phoenix_message(f"app:{client_id}", "phx_join", {})
            await app_ws.send(join_msg)
            await asyncio.wait_for(app_ws.recv(), timeout=TIMEOUT)
            
            # List servers
            list_msg = phoenix_message(
                f"app:{client_id}",
                "list_servers",
                {}
            )
            await app_ws.send(list_msg)
            log(f"  → Sent list_servers request", Colors.YELLOW)
            
            response = await asyncio.wait_for(app_ws.recv(), timeout=TIMEOUT)
            data = json.loads(response)
            
            if data['event'] == 'phx_reply' and data['payload']['status'] == 'ok':
                servers = data['payload']['response']['servers']
                log(f"  ← Received: {len(servers)} servers", Colors.YELLOW)
                
                found = any(s['server_id'] == server_id for s in servers)
                
                if found:
                    log(f"  ✓ Found registered server in list", Colors.GREEN)
                else:
                    log(f"  ⚠ Server not found in list", Colors.YELLOW)
            else:
                log(f"  ⚠ Unexpected response: {data}", Colors.YELLOW)
        
        await server_ws.close()
        log(f"✅ List servers successful\n", Colors.GREEN)
        return True
        
    except Exception as e:
        log(f"❌ List servers failed: {e}\n", Colors.RED)
        return False


async def test_pairing_flow():
    """Test complete pairing flow between server and app."""
    log("🧪 Test 3: Pairing Flow", Colors.BLUE)
    
    server_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    pairing_code = None
    
    try:
        # Connect server
        server_ws = await websockets.connect(f"{BRIDGE_URL}?type=server")
        
        join_msg = phoenix_message(f"server:{server_id}", "phx_join", {})
        await server_ws.send(join_msg)
        await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
        
        register_msg = phoenix_message(
            f"server:{server_id}",
            "register",
            {
                "server_id": server_id,
                "display_name": "Test Server for Pairing",
                "computer_name": "test-pair.local",
                "location": None
            }
        )
        
        await server_ws.send(register_msg)
        await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
        log(f"  ✓ Server registered", Colors.GREEN)
        
        await asyncio.sleep(0.5)
        
        # Connect app
        app_ws = await websockets.connect(f"{BRIDGE_URL}?type=app")
        log(f"  ✓ App connected", Colors.GREEN)
        
        join_msg = phoenix_message(f"app:{client_id}", "phx_join", {})
        await app_ws.send(join_msg)
        await asyncio.wait_for(app_ws.recv(), timeout=TIMEOUT)
        
        # Request pairing
        pair_request_msg = phoenix_message(
            f"app:{client_id}",
            "pair_request",
            {
                "server_id": server_id
            }
        )
        
        await app_ws.send(pair_request_msg)
        log(f"  → Sent pairing request", Colors.YELLOW)
        
        # App should receive confirmation
        app_response = await asyncio.wait_for(app_ws.recv(), timeout=TIMEOUT)
        app_data = json.loads(app_response)
        log(f"  ← App received: {app_data['event']}", Colors.YELLOW)
        
        # Server should receive pairing code
        server_response = await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
        server_data = json.loads(server_response)
        
        if server_data['event'] == 'pairing_requested':
            pairing_code = server_data['payload']['code']
            log(f"  ← Server received code: {pairing_code}", Colors.YELLOW)
        else:
            log(f"  ⚠ Unexpected server response: {server_data}", Colors.YELLOW)
        
        if pairing_code:
            # Submit pairing code
            pair_submit_msg = phoenix_message(
                f"app:{client_id}",
                "pair_submit",
                {
                    "server_id": server_id,
                    "code": pairing_code
                }
            )
            
            await app_ws.send(pair_submit_msg)
            log(f"  → Submitted pairing code", Colors.YELLOW)
            
            # App should receive session_id
            app_response = await asyncio.wait_for(app_ws.recv(), timeout=TIMEOUT)
            app_data = json.loads(app_response)
            
            if app_data['event'] == 'phx_reply' and app_data['payload']['status'] == 'ok':
                response_payload = app_data['payload']['response']
                session_id = response_payload['session_id']
                pairing_token = response_payload.get('pairing_token')
                log(f"  ✓ App received session_id: {session_id[:8]}...", Colors.GREEN)

                if not pairing_token:
                    log(f"  ⚠ No pairing_token in app response: {app_data}", Colors.YELLOW)
                    await server_ws.close()
                    await app_ws.close()
                    return False
                if "." not in pairing_token:
                    log(f"  ⚠ pairing_token is not signed: {pairing_token}", Colors.YELLOW)
                    await server_ws.close()
                    await app_ws.close()
                    return False
                log(f"  ✓ App received pairing_token", Colors.GREEN)
                
                # Server should receive paired notification
                server_response = await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
                server_data = json.loads(server_response)
                
                if server_data['event'] == 'paired':
                    log(f"  ✓ Server received paired notification", Colors.GREEN)

                    # Reconnect as an app and resume with the pairing token.
                    # The resumed bridge session id should be fresh; the token
                    # is the durable logical pairing identity.
                    await app_ws.close()
                    resumed_client_id = str(uuid.uuid4())
                    resume_ws = await websockets.connect(f"{BRIDGE_URL}?type=app")

                    join_msg = phoenix_message(f"app:{resumed_client_id}", "phx_join", {})
                    await resume_ws.send(join_msg)
                    await asyncio.wait_for(resume_ws.recv(), timeout=TIMEOUT)

                    resume_msg = phoenix_message(
                        f"app:{resumed_client_id}",
                        "resume_session",
                        {
                            "server_id": server_id,
                            "pairing_token": pairing_token
                        }
                    )
                    await resume_ws.send(resume_msg)
                    log(f"  → Sent resume_session", Colors.YELLOW)

                    resume_response = await asyncio.wait_for(resume_ws.recv(), timeout=TIMEOUT)
                    resume_data = json.loads(resume_response)

                    if resume_data['event'] != 'phx_reply' or resume_data['payload']['status'] != 'ok':
                        log(f"  ⚠ Resume failed: {resume_data}", Colors.YELLOW)
                        await server_ws.close()
                        await resume_ws.close()
                        return False

                    resumed_session_id = resume_data['payload']['response']['session_id']
                    if resumed_session_id == session_id:
                        log(f"  ⚠ Resume reused session_id: {resumed_session_id}; response={resume_data}", Colors.YELLOW)
                        await server_ws.close()
                        await resume_ws.close()
                        return False

                    log(
                        f"  ✓ Resume returned fresh session_id: {resumed_session_id[:8]}...",
                        Colors.GREEN
                    )

                    server_response = await asyncio.wait_for(server_ws.recv(), timeout=TIMEOUT)
                    server_data = json.loads(server_response)
                    if server_data['event'] != 'paired':
                        log(f"  ⚠ Server did not receive resumed paired event: {server_data}", Colors.YELLOW)
                        await server_ws.close()
                        await resume_ws.close()
                        return False

                    log(f"  ✓ Server received resumed paired notification", Colors.GREEN)
                    log(f"✅ Pairing flow successful\n", Colors.GREEN)
                    
                    await server_ws.close()
                    await resume_ws.close()
                    return True
            else:
                log(f"  ⚠ No session_id in app response: {app_data}", Colors.YELLOW)
        
        await server_ws.close()
        await app_ws.close()
        log(f"⚠️ Pairing flow incomplete\n", Colors.YELLOW)
        return False
        
    except Exception as e:
        log(f"❌ Pairing flow failed: {e}\n", Colors.RED)
        return False


async def main():
    log("=" * 60)
    log("🚀 Bridge Service Docker Integration Tests", Colors.BLUE)
    log("=" * 60)
    log("")
    
    results = []
    
    # Test 1: Server Registration
    result, _ = await test_server_registration()
    results.append(result)
    
    # Test 2: List Servers
    result = await test_list_servers()
    results.append(result)
    
    # Test 3: Pairing Flow
    result = await test_pairing_flow()
    results.append(result)
    
    # Summary
    log("=" * 60)
    log("📊 Test Summary", Colors.BLUE)
    log("=" * 60)
    passed = sum(results)
    total = len(results)
    
    log(f"Passed: {passed}/{total}", Colors.GREEN if passed == total else Colors.YELLOW)
    
    if passed == total:
        log("🎉 All tests passed!", Colors.GREEN)
        return 0
    else:
        log(f"⚠️  Some tests failed", Colors.YELLOW)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n🛑 Tests interrupted", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        log(f"\n💥 Fatal error: {e}", Colors.RED)
        sys.exit(1)
