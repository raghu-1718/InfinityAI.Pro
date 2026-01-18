# ✅ Phase 4: User Acceptance Testing (UAT) - EXECUTION PLAN

**Date**: January 20, 2026
**Timeline**: 4 hours
**Status**: 🟢 **UAT READY TO EXECUTE**
**Sign-Off Authority**: Product Manager

---

## 🎯 Phase 4 Objectives

### Primary Goals

1. ✅ **Test Account Setup Workflow** (30 min)
   - User registration via Google
   - Profile completion
   - Account preferences
   - Data persistence

2. ✅ **Test DhanHQ Connection** (30 min)
   - OAuth integration
   - Credential verification
   - Account linking
   - Permission validation

3. ✅ **Test Paper Trading Execution** (45 min)
   - Order placement (MARKET, LIMIT, STOPLOSS)
   - Order confirmation
   - Position tracking
   - P&L calculation
   - Portfolio management

4. ✅ **Test Dashboard Functionality** (30 min)
   - Dashboard layout
   - Real-time data display
   - Chart rendering
   - Widget responsiveness

5. ✅ **Test Mobile Access** (15 min)
   - Mobile responsiveness
   - Touch interactions
   - Mobile-specific features
   - Connection handling

---

## 📋 UAT Test Scenarios

### Scenario 1: Account Setup Workflow

**Objective**: Verify user can create account and set up profile

**Test Steps**:

1. **Launch Application**
   - Navigate to: `https://galvanic-pulsar-482815-h0.web.app`
   - Expected: Page loads within 3 seconds
   - Status: ⏳ Pending

2. **Sign in with Google**
   - Click "Sign in with Google"
   - Select/authenticate Google account
   - Expected: Redirect to dashboard within 5 seconds
   - Status: ⏳ Pending

3. **Complete User Profile**
   - Fill in full name
   - Fill in email (auto-filled from Google)
   - Select trading experience level
   - Accept terms of service
   - Click "Save Profile"
   - Expected: Profile saved, confirmation message displayed
   - Status: ⏳ Pending

4. **Verify Data Persistence**
   - Reload page
   - Expected: Profile data remains populated
   - Status: ⏳ Pending

**Success Criteria**:

- ✅ Account created successfully
- ✅ Profile information saved
- ✅ Data persists after page reload
- ✅ No error messages
- ✅ Smooth user experience

---

### Scenario 2: DhanHQ Connection

**Objective**: Verify user can connect DhanHQ broker account

**Test Steps**:

1. **Navigate to Settings**
   - Click "Settings" or "Account Settings"
   - Expected: Settings page loads
   - Status: ⏳ Pending

2. **Locate Broker Connection**
   - Find "Connected Brokers" or "DhanHQ Settings"
   - Expected: Section visible and accessible
   - Status: ⏳ Pending

3. **Initiate DhanHQ Connection**
   - Click "Connect DhanHQ Account"
   - Expected: OAuth dialog appears (or redirect to DhanHQ)
   - Status: ⏳ Pending

4. **Complete DhanHQ OAuth**
   - Authenticate with DhanHQ sandbox account
   - Grant permissions
   - Expected: Redirect back to app, connection confirmed
   - Status: ⏳ Pending

5. **Verify Connection Status**
   - Expected: "Connected" status displayed
   - Expected: Account ID visible
   - Expected: "Disconnect" option available
   - Status: ⏳ Pending

6. **Test Credential Validation**
   - Verify credentials are securely stored
   - Verify no sensitive data in logs
   - Expected: No security warnings
   - Status: ⏳ Pending

**Success Criteria**:

- ✅ Connection successful
- ✅ Status displayed correctly
- ✅ Credentials secure
- ✅ Account information accessible
- ✅ No error messages

---

### Scenario 3: Paper Trading Execution

**Objective**: Verify paper trading mode works correctly

**Test Steps**:

1. **Verify Trading Mode**
   - Check dashboard for "Paper Trading Mode" indicator
   - Expected: Clearly visible, states "PAPER TRADING"
   - Status: ⏳ Pending

2. **Place Market Order**
   - Navigate to "Trade" or "Place Order"
   - Select symbol (e.g., NIFTY50, BANKNIFTY)
   - Select "Market" order type
   - Enter quantity (e.g., 1 lot)
   - Click "Place Order"
   - Expected: Order confirmed within 2 seconds
   - Expected: "Paper Order #XXXXX" confirmation message
   - Status: ⏳ Pending

3. **Verify Order in Portfolio**
   - Check "Positions" or "Active Orders"
   - Expected: Order appears with correct symbol, quantity, price
   - Expected: Current P&L shown
   - Status: ⏳ Pending

4. **Place Limit Order**
   - Place limit order with custom price
   - Expected: Order placed successfully
   - Expected: Shows as "Pending" until filled
   - Status: ⏳ Pending

5. **Test Order Cancellation**
   - Cancel the limit order
   - Expected: Order status changes to "Cancelled"
   - Expected: Position updates correctly
   - Status: ⏳ Pending

6. **Verify P&L Calculation**
   - Check portfolio P&L values
   - Manual verification: (Current Price - Entry Price) × Quantity
   - Expected: Calculated values match manual verification
   - Status: ⏳ Pending

7. **Test Multiple Positions**
   - Place 3-5 different orders
   - Expected: All positions tracked correctly
   - Expected: Portfolio P&L aggregates correctly
   - Status: ⏳ Pending

**Success Criteria**:

- ✅ All orders execute successfully
- ✅ P&L calculations accurate
- ✅ Positions tracked correctly
- ✅ Order history maintained
- ✅ No real money at risk (paper mode confirmed)

---

### Scenario 4: Dashboard Functionality

**Objective**: Verify dashboard displays data correctly and responds to interactions

**Test Steps**:

1. **Dashboard Load**
   - Navigate to dashboard
   - Expected: Loads within 3 seconds
   - Expected: All widgets visible
   - Status: ⏳ Pending

2. **Portfolio Widget**
   - Verify portfolio value displays
   - Verify P&L shows correctly
   - Verify portfolio allocation pie chart renders
   - Expected: All data accurate and updated
   - Status: ⏳ Pending

3. **Market Data Widget**
   - Verify market indices show (NIFTY50, BANKNIFTY, etc.)
   - Verify real-time updates (refresh every 5 seconds)
   - Expected: Data updates smoothly
   - Status: ⏳ Pending

4. **Signals Widget**
   - Verify AI-generated signals display
   - Verify signal strength indicators show
   - Expected: Signals relevant to market conditions
   - Status: ⏳ Pending

5. **Recent Orders Widget**
   - Verify recent orders listed
   - Verify order details accurate
   - Expected: Orders sorted by time (newest first)
   - Status: ⏳ Pending

6. **Widget Interactions**
   - Click on widgets to expand/collapse
   - Drag widgets to reorder (if supported)
   - Expected: Smooth animations, responsive
   - Status: ⏳ Pending

7. **Refresh Data**
   - Click "Refresh" button
   - Expected: All widgets update within 2 seconds
   - Status: ⏳ Pending

**Success Criteria**:

- ✅ All widgets load and display correctly
- ✅ Data updates in real-time
- ✅ Dashboard responsive to user interactions
- ✅ No missing or incorrect data
- ✅ Performance smooth (no lag)

---

### Scenario 5: Mobile Access Verification

**Objective**: Verify application works on mobile devices

**Test Steps**:

1. **Access on Mobile Browser**
   - Open application on mobile device (iOS or Android)
   - Navigate to: `https://galvanic-pulsar-482815-h0.web.app`
   - Expected: Page loads and adapts to screen size
   - Status: ⏳ Pending

2. **Responsive Layout**
   - Verify layout adapts to mobile screen
   - Verify no horizontal scrolling needed
   - Expected: Content readable without zooming
   - Status: ⏳ Pending

3. **Touch Interactions**
   - Test button clicks on mobile
   - Test form input on mobile
   - Expected: All inputs responsive to touch
   - Status: ⏳ Pending

4. **Mobile-Specific Features**
   - Verify mobile menu/hamburger works
   - Verify bottom navigation (if applicable)
   - Expected: Navigation functional on mobile
   - Status: ⏳ Pending

5. **Performance on Mobile**
   - Measure page load time on mobile
   - Expected: Loads within 5 seconds on 4G
   - Status: ⏳ Pending

6. **Network Resilience**
   - Test with different network conditions (WiFi, 4G, 3G simulation)
   - Expected: Application handles network changes gracefully
   - Status: ⏳ Pending

**Success Criteria**:

- ✅ Mobile layout responsive and readable
- ✅ All touch interactions work
- ✅ Performance acceptable on mobile
- ✅ No broken layouts
- ✅ Network resilience verified

---

## ✅ UAT Validation Checklist

### Pre-UAT Verification

**Environment Ready**:

- [x] Staging services verified healthy (Phase 3)
- [x] Paper trading mode enabled
- [x] Database configured for testing
- [x] Test data prepared
- [x] Browser testing tools ready

**Test Accounts Ready**:

- [x] Google account for testing
- [x] DhanHQ sandbox account for testing
- [x] Mobile device(s) for testing
- [x] Multiple browsers available

**Documentation Ready**:

- [x] Test scenarios documented
- [x] Expected outcomes defined
- [x] Success criteria established
- [x] Issue tracking template ready

### Test Execution Sign-Off

**Scenario 1: Account Setup** ⏳ Pending

- [ ] All test steps completed
- [ ] No blocking issues found
- [ ] User experience acceptable
- [ ] QA Lead sign-off

**Scenario 2: DhanHQ Connection** ⏳ Pending

- [ ] All test steps completed
- [ ] Connection secure
- [ ] Credentials properly encrypted
- [ ] QA Lead sign-off

**Scenario 3: Paper Trading** ⏳ Pending

- [ ] All order types tested
- [ ] P&L calculations verified
- [ ] Position tracking accurate
- [ ] QA Lead sign-off

**Scenario 4: Dashboard** ⏳ Pending

- [ ] All widgets functional
- [ ] Data updates correctly
- [ ] Performance acceptable
- [ ] QA Lead sign-off

**Scenario 5: Mobile Access** ⏳ Pending

- [ ] Mobile layout responsive
- [ ] Touch interactions work
- [ ] Performance acceptable
- [ ] QA Lead sign-off

### Overall UAT Sign-Off

**Product Manager Sign-Off**: ⏳ Pending

- [ ] All scenarios passed
- [ ] User experience meets requirements
- [ ] No P1/P2 issues
- [ ] Ready for Phase 5 (Performance Testing)

---

## 🐛 Issue Tracking Template

### Issue Report Format

For any issues found during UAT:

```
Issue ID: UAT-001
Severity: P1 (Blocking) | P2 (High) | P3 (Medium) | P4 (Low)
Component: Dashboard | Trading | Account | Mobile
Title: [Brief description]

Description:
[Detailed description of the issue]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Expected Behavior:
[What should happen]

Actual Behavior:
[What actually happens]

Screenshots/Logs:
[Attach relevant screenshots or error logs]

Resolution:
[To be filled by engineering team]

Status: Open | In Progress | Fixed | Verified
```

### Issue Severity Definitions

- **P1 (Blocking)**: Prevents core functionality, must fix before production
- **P2 (High)**: Significant impact on user experience, should fix before production
- **P3 (Medium)**: Minor impact, can fix post-launch if needed
- **P4 (Low)**: Cosmetic or very minor, can defer to future sprint

---

## 📊 UAT Timeline

| Test Scenario           | Duration    | Status       |
| ----------------------- | ----------- | ------------ |
| Account Setup           | 30 min      | ⏳ Pending   |
| DhanHQ Connection       | 30 min      | ⏳ Pending   |
| Paper Trading           | 45 min      | ⏳ Pending   |
| Dashboard               | 30 min      | ⏳ Pending   |
| Mobile Access           | 15 min      | ⏳ Pending   |
| Issue Review & Sign-Off | 30 min      | ⏳ Pending   |
| **TOTAL**               | **4 hours** | **⏳ READY** |

---

## 🎯 UAT Success Criteria

### Must Have (Blocking) ✅

- [ ] Account setup works without errors
- [ ] DhanHQ connection successful
- [ ] Paper trading orders execute
- [ ] Dashboard displays correctly
- [ ] Mobile responsive
- [ ] Zero P1 issues
- [ ] Zero P2 issues (unless deferred with approval)

### Should Have ✅

- [ ] Performance baseline met
- [ ] All user workflows smooth
- [ ] Helpful error messages
- [ ] Intuitive UI/UX

### Nice to Have

- [ ] Advanced features working
- [ ] Customization options available
- [ ] Accessibility features

---

## 🔄 UAT Team Assignments

**Product Manager**: Requirement verification, sign-off authority
**QA Lead**: Test execution, issue documentation, quality gate
**Engineering Lead**: Technical support, troubleshooting assistance
**Users/Beta Testers**: User workflow validation, feedback

---

## ⏭️ Phase 5 Preparation

### Performance Testing (After UAT approval)

**Scope**:

- Load testing: 1000 concurrent users
- Latency testing: Target p95 <1000ms
- Error rate: Target <0.1%
- Resource monitoring: CPU, memory, network

**Timeline**: 4 hours (after UAT sign-off)

---

## 📋 PHASE 4 READINESS SUMMARY

**Status**: 🟢 **READY TO EXECUTE**

**Prerequisites Met**:

- ✅ Phase 1-3 complete
- ✅ All services healthy
- ✅ Test accounts ready
- ✅ Test scenarios documented
- ✅ Success criteria defined
- ✅ Issue tracking ready

**Test Coverage**:

- Account workflows ✅
- Broker integration ✅
- Trading functionality ✅
- UI/Dashboard ✅
- Mobile compatibility ✅

**Risk Assessment**: LOW

- All critical services operational
- Test scenarios comprehensive
- Rollback procedures ready
- Team expertise available

**Next Action**: Execute UAT test scenarios above

---

**Phase 4 UAT Plan Created**: January 20, 2026
**Status**: ✅ READY FOR EXECUTION
**Sign-Off Authority**: Product Manager
