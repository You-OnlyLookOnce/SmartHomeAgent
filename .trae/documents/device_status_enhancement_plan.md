# Device Status Management Enhancement - Implementation Plan

## Overview
This plan outlines the comprehensive enhancement of device status management, including frontend visual improvements, backend API development, MCP integration, and thorough testing.

## Current State Analysis

### Existing Implementation
- **Frontend**: Basic device cards with online/offline status, simple status info display
- **Backend**: `/api/devices` endpoint returns device list with `current_state` field
- **MCP**: DeviceMCPAdapter manages device state with `current_state` dictionary
- **Status Fields**: `device_id`, `device_name`, `device_type`, `current_state`, `last_updated`

### Identified Gaps
1. No dedicated device status API endpoint
2. Limited visual status representation (only online/offline badge)
3. No real-time status updates (manual refresh required)
4. No status filtering or sorting capabilities
5. No authentication/authorization on device endpoints
6. No rate limiting on API calls
7. MCP doesn't notify agent of status changes proactively

---

## Task 1: Frontend Status Display Enhancement
**Priority**: P0
**Depends On**: None

### Description
Enhance the frontend device display interface with comprehensive status visualization, real-time updates, and filtering capabilities.

### Implementation Details

#### 1.1 Enhanced Device Card Design
- Add color-coded status indicators:
  - 🟢 Online (active)
  - 🟡 Online (idle/inactive for >5 min)
  - 🔴 Offline
  - ⚠️ Error state
- Display detailed status information:
  - Lamp: Power state, brightness %, color temperature
  - AC: Power state, temperature, mode (cool/heat), fan speed
  - Curtain: Position %, open/closed state
- Add "last seen" timestamp
- Show connection quality indicator (WiFi signal strength)

#### 1.2 Real-Time Status Updates
- Implement WebSocket connection for live status updates
- Fallback to polling (every 5 seconds) if WebSocket unavailable
- Add visual "updating" indicator during refresh
- Smooth transition animations for status changes

#### 1.3 Status Filtering & Sorting
- Add filter controls:
  - By status: All, Online, Offline, Error
  - By type: All, Lamp, AC, Curtain
  - By activity: Active, Idle, Inactive
- Add sorting options:
  - By name (A-Z, Z-A)
  - By status (Online first, Offline first)
  - By last activity time
  - By device type

#### 1.4 Status Dashboard Widget
- Add summary statistics at top of device list:
  - Total devices count
  - Online/Offline counts
  - Active devices count
  - Recent status changes

### Success Criteria
- Device cards display comprehensive status information
- Status updates reflect in real-time without page refresh
- Filtering and sorting work correctly
- UI remains responsive with many devices

### Test Requirements
- **TR-1.1** (programmatic): WebSocket connection establishes successfully
- **TR-1.2** (programmatic): Status polling falls back correctly when WebSocket fails
- **TR-1.3** (human-judgement): Status indicators are visually clear and intuitive
- **TR-1.4** (human-judgement): Filtering and sorting work smoothly

---

## Task 2: Backend API Development
**Priority**: P0
**Depends On**: None

### Description
Design and implement RESTful API endpoints for device status management with proper security, validation, and rate limiting.

### Implementation Details

#### 2.1 New API Endpoints

```
GET /api/devices/status
- Returns status summary for all devices
- Response: { "success": true, "devices": [...], "summary": {...} }

GET /api/devices/{device_id}/status
- Returns detailed status for specific device
- Response: { "success": true, "device_id": "...", "status": {...}, "timestamp": "..." }

GET /api/devices/{device_id}/history
- Returns status history (last 24h by default)
- Query params: ?hours=24, ?start_time=..., ?end_time=...
- Response: { "success": true, "device_id": "...", "history": [...] }

POST /api/devices/{device_id}/refresh
- Force refresh device status from physical device
- Rate limited: max 1 request per 10 seconds per device
- Response: { "success": true, "status": {...} }

GET /api/devices/status/stream
- WebSocket endpoint for real-time status updates
- Authentication required
- Sends updates when device status changes
```

#### 2.2 Authentication & Authorization
- Implement JWT token authentication
- Add role-based access control:
  - `admin`: Full access
  - `user`: Read-only access to status
  - `service`: System-level access for MCP
- Add API key authentication for MCP integration

#### 2.3 Rate Limiting
- Implement rate limiting using Redis/memory store:
  - General endpoints: 100 requests/minute per IP
  - Status refresh: 6 requests/minute per device
  - WebSocket: Max 5 concurrent connections per user
- Return 429 status code with retry-after header when limit exceeded

#### 2.4 Request Validation
- Validate all request parameters using Pydantic models
- Sanitize device_id to prevent injection attacks
- Validate timestamp formats
- Limit history query range (max 7 days)

#### 2.5 Standardized Response Format
```json
{
  "success": true/false,
  "data": { ... },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  },
  "meta": {
    "timestamp": "2026-03-26T12:00:00Z",
    "request_id": "uuid",
    "pagination": { ... }
  }
}
```

### Success Criteria
- All new endpoints return correct JSON responses
- Authentication blocks unauthorized access
- Rate limiting prevents API abuse
- Validation rejects malformed requests

### Test Requirements
- **TR-2.1** (programmatic): All endpoints return 200 for valid requests
- **TR-2.2** (programmatic): Authentication returns 401 for missing/invalid tokens
- **TR-2.3** (programmatic): Rate limiting returns 429 after threshold exceeded
- **TR-2.4** (programmatic): Validation returns 400 for invalid parameters
- **TR-2.5** (programmatic): WebSocket accepts authenticated connections

---

## Task 3: MCP (Master Control Program) Updates
**Priority**: P1
**Depends On**: Task 2

### Description
Enhance the MCP to integrate with the new status API, track device status changes, and notify the intelligent agent proactively.

### Implementation Details

#### 3.1 MCP Status Integration
- Add method `subscribe_to_status_updates(device_ids: List[str])` to DeviceMCPAdapter
- Implement status caching with TTL (5 minutes)
- Add method `get_cached_status(device_id: str)` for quick access
- Implement batch status retrieval for multiple devices

#### 3.2 Status Change Notification System
- Add callback system for status changes:
  ```python
  class StatusChangeCallback:
      def on_status_change(self, device_id: str, old_status: dict, new_status: dict)
      def on_device_offline(self, device_id: str, last_seen: datetime)
      def on_device_online(self, device_id: str)
  ```
- Implement agent notification via internal message bus
- Add priority levels for different status changes:
  - HIGH: Device offline, error states
  - MEDIUM: Significant state changes (e.g., AC turned on)
  - LOW: Minor updates (e.g., brightness change)

#### 3.3 Agent Awareness Integration
- Create `DeviceStatusAwareness` module in agent system
- Implement proactive notifications to agent:
  - "Device X has gone offline"
  - "Device Y status changed from A to B"
  - "Multiple devices are offline"
- Add context enrichment for agent (e.g., "User's bedroom lamp is off")

#### 3.4 MCP Internal Documentation
- Add docstrings to all new methods
- Create `docs/MCP_DEVICE_STATUS.md` with:
  - Architecture overview
  - API usage examples
  - Configuration options
  - Troubleshooting guide

#### 3.5 Status Persistence
- Add optional status history logging
- Implement status change event log
- Store critical status changes to database

### Success Criteria
- MCP receives real-time status updates
- Agent is notified of important status changes
- Status caching improves performance
- Documentation is complete and accurate

### Test Requirements
- **TR-3.1** (programmatic): Status callbacks trigger on device state change
- **TR-3.2** (programmatic): Agent receives notification within 1 second of change
- **TR-3.3** (programmatic): Status cache returns correct data within TTL
- **TR-3.4** (human-judgement): Agent notifications are contextually appropriate

---

## Task 4: Integration and Testing
**Priority**: P1
**Depends On**: Task 1, Task 2, Task 3

### Description
Ensure proper integration between all components and implement comprehensive testing.

### Implementation Details

#### 4.1 Integration Testing
- Test complete flow: Device → MCP → Backend API → Frontend
- Verify WebSocket real-time updates end-to-end
- Test authentication flow across all components
- Verify rate limiting works in production-like scenarios

#### 4.2 Unit Tests

**Backend Tests** (`tests/api/test_device_status.py`):
```python
class TestDeviceStatusAPI:
    def test_get_device_status_success(self)
    def test_get_device_status_not_found(self)
    def test_get_device_status_unauthorized(self)
    def test_refresh_status_rate_limit(self)
    def test_websocket_authentication(self)
    def test_status_history_query(self)
```

**MCP Tests** (`tests/mcp/test_device_status.py`):
```python
class TestDeviceMCPStatus:
    def test_status_subscription(self)
    def test_status_change_callback(self)
    def test_status_caching(self)
    def test_agent_notification(self)
```

**Frontend Tests** (`tests/frontend/test_device_status.js`):
```javascript
describe('Device Status UI', () => {
    test('renders status indicators correctly')
    test('updates status in real-time')
    test('filtering works as expected')
    test('sorting changes device order')
})
```

#### 4.3 End-to-End Tests
- Scenario 1: User views device list, sees real-time status updates
- Scenario 2: Device goes offline, agent is notified, UI updates
- Scenario 3: User filters devices by status, then clears filter
- Scenario 4: Rate limit triggered, appropriate error shown

#### 4.4 Performance Testing
- Load test: 100 concurrent users viewing device status
- Stress test: 1000 devices with status updates every second
- Measure API response times (target: <100ms for status endpoints)
- Measure WebSocket latency (target: <50ms)

#### 4.5 Documentation
- Create `docs/API_DEVICE_STATUS.md`:
  - Endpoint specifications
  - Authentication guide
  - Rate limit details
  - Example requests/responses
  - Error codes reference

- Create `docs/FRONTEND_DEVICE_STATUS.md`:
  - Component documentation
  - State management guide
  - WebSocket usage
  - Customization options

- Update main README with new features

### Success Criteria
- All integration tests pass
- Unit test coverage >80% for new code
- End-to-end scenarios work correctly
- Performance meets targets
- Documentation is complete

### Test Requirements
- **TR-4.1** (programmatic): All unit tests pass
- **TR-4.2** (programmatic): All integration tests pass
- **TR-4.3** (programmatic): API response time <100ms (95th percentile)
- **TR-4.4** (programmatic): WebSocket latency <50ms (95th percentile)
- **TR-4.5** (human-judgement): End-to-end scenarios work smoothly

---

## Task 5: Deployment and Rollback Plan
**Priority**: P2
**Depends On**: Task 4

### Description
Plan for safe deployment with rollback capabilities.

### Implementation Details

#### 5.1 Deployment Steps
1. Deploy backend API changes (backward compatible)
2. Update MCP with new status features
3. Deploy frontend changes
4. Enable WebSocket server
5. Monitor for errors

#### 5.2 Rollback Plan
- Feature flags for new functionality
- Database migration rollback scripts
- Frontend version pinning
- MCP fallback to old status mechanism

#### 5.3 Monitoring
- Add logging for all status API calls
- Monitor WebSocket connection counts
- Track rate limit hits
- Alert on error rates >1%

### Success Criteria
- Zero-downtime deployment
- Rollback completes within 5 minutes if needed
- Monitoring captures all critical metrics

---

## Implementation Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| Task 1: Frontend Enhancement | 3 days | None |
| Task 2: Backend API | 4 days | None |
| Task 3: MCP Updates | 3 days | Task 2 |
| Task 4: Integration & Testing | 4 days | Task 1, 2, 3 |
| Task 5: Deployment | 1 day | Task 4 |
| **Total** | **15 days** | - |

---

## Files to Modify

### Frontend
- `src/frontend/static/js/app.js` - Device status UI logic
- `src/frontend/static/css/style.css` - Status indicator styles
- `src/frontend/templates/index.html` - Device card templates

### Backend
- `src/gateway/api_gateway.py` - New API endpoints
- `src/core/device_manager.py` - Status management
- `src/skills/mcp_skills/device_mcp_adapter.py` - MCP integration

### New Files
- `src/gateway/auth_middleware.py` - Authentication
- `src/gateway/rate_limiter.py` - Rate limiting
- `src/agent/device_status_awareness.py` - Agent integration
- `tests/api/test_device_status.py` - API tests
- `tests/mcp/test_device_status.py` - MCP tests
- `docs/API_DEVICE_STATUS.md` - API documentation
- `docs/MCP_DEVICE_STATUS.md` - MCP documentation

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| WebSocket performance issues | High | Implement fallback polling |
| Rate limiting too aggressive | Medium | Start with generous limits |
| Authentication complexity | Medium | Use existing auth system |
| Breaking changes to existing API | High | Maintain backward compatibility |
| MCP notification flooding | Medium | Implement priority queue |

---

## Success Metrics

- API response time <100ms (95th percentile)
- WebSocket latency <50ms (95th percentile)
- Test coverage >80%
- Zero critical bugs in production
- User satisfaction score >4/5
