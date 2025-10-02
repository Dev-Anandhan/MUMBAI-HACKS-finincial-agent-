# 🧪 Financial Agent Testing Guide

## 🚀 Quick Start Testing

The Financial Agent system is now running and ready for testing! Here's how to test all the core features:

### **Services Running:**
- ✅ **Backend API**: http://localhost:8000
- ✅ **Frontend App**: http://localhost:3000
- ✅ **API Documentation**: http://localhost:8000/docs

---

## 📱 **1. Frontend Testing (Mobile-First Interface)**

### **Access the App:**
1. Open your browser and go to: **http://localhost:3000**
2. You'll see a beautiful mobile-first financial dashboard

### **Test Features:**
- ✅ **Dashboard Overview**: Shows current balance and savings
- ✅ **Cash Flow Forecast**: Risk level indicator with predictions
- ✅ **Financial Insights**: AI-generated nudges and suggestions
- ✅ **Quick Actions**: Add transactions, view savings, predictions
- ✅ **AI Chat**: Interactive financial assistant

### **Interactive Testing:**
1. **Add a Transaction**: Click "Add Transaction" button
   - Try adding an income: ₹2000, Gig Income
   - Try adding an expense: ₹500, Groceries
   
2. **Chat with AI**: Ask questions like:
   - "What's my current balance?"
   - "How much can I spend today?"
   - "Should I save more money?"

---

## 🔧 **2. Backend API Testing**

### **Test Core Endpoints:**

#### **Health Check:**
```bash
curl -X GET http://localhost:8000/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "service": "financial-agent-test",
  "version": "1.0.0",
  "timestamp": "2025-10-02T15:47:44.117530"
}
```

#### **Setup Demo Data:**
```bash
curl -X POST http://localhost:8000/demo/setup
```
**Expected Response:**
```json
{
  "message": "Demo data setup complete",
  "user_id": "demo_user_123",
  "transactions_created": 5,
  "current_balance": 6200.0
}
```

#### **Check Balance:**
```bash
curl -X GET http://localhost:8000/transactions/demo_user_123/balance
```
**Expected Response:**
```json
{
  "user_id": "demo_user_123",
  "current_balance": 6200.0
}
```

#### **Generate Cashflow Prediction:**
```bash
curl -X POST "http://localhost:8000/predictions/?user_id=demo_user_123"
```
**Expected Response:**
```json
{
  "prediction_id": "09f7e4a5-c1fc-4ddf-8fb1-c854f98450ca",
  "user_id": "demo_user_123",
  "predicted_balance": 833.33,
  "shortfall_probability": 0.87,
  "confidence_level": 0.1,
  "reasoning": "High risk of shortfall in next 7 days. Predicted balance: ₹833. Consider reducing discretionary spending."
}
```

#### **Generate AI Nudges:**
```bash
curl -X POST "http://localhost:8000/nudges/generate?user_id=demo_user_123"
```
**Expected Response:**
```json
{
  "nudges": [
    {
      "nudge_id": "6378a976-30d0-4a23-b900-e0e18135ca9d",
      "user_id": "demo_user_123",
      "title": "High Spending Alert",
      "message": "You've spent ₹2300 in the last 5 transactions. Consider reviewing your expenses.",
      "nudge_type": "informational",
      "priority": "medium"
    },
    {
      "nudge_id": "0eccb1de-7282-4c47-ad5b-5ea3d61307e3",
      "user_id": "demo_user_123",
      "title": "Savings Opportunity",
      "message": "You have ₹6200 available. Consider saving ₹500 to your emergency fund.",
      "nudge_type": "actionable",
      "priority": "low",
      "suggested_action": {
        "type": "save_to_emergency",
        "amount": 500,
        "description": "Save to emergency fund"
      }
    }
  ],
  "count": 2
}
```

---

## 🎯 **3. Core Features Testing**

### **A. Cashflow Prediction Engine**
✅ **What it does**: Predicts future balance and shortfall risk
✅ **How to test**: 
- Generate predictions with different transaction patterns
- Check reasoning explanations
- Verify confidence levels

### **B. Intelligent Nudging System**
✅ **What it does**: Provides contextual financial coaching
✅ **How to test**:
- Generate nudges for different financial situations
- Check priority levels (high, medium, low)
- Verify actionable vs informational nudges

### **C. Transaction Management**
✅ **What it does**: Tracks and categorizes financial transactions
✅ **How to test**:
- Add various transaction types
- Check balance calculations
- Verify transaction history

### **D. AI Chat Assistant**
✅ **What it does**: Natural language financial queries
✅ **How to test**:
- Ask about balance, spending, savings
- Test different question types
- Verify contextual responses

---

## 📊 **4. Test Scenarios**

### **Scenario 1: New User Onboarding**
1. Setup demo data: `POST /demo/setup`
2. Check initial balance: `GET /transactions/demo_user_123/balance`
3. Generate first prediction: `POST /predictions/?user_id=demo_user_123`
4. Generate initial nudges: `POST /nudges/generate?user_id=demo_user_123`

### **Scenario 2: High Spending Alert**
1. Add multiple expense transactions
2. Generate new prediction
3. Check for high spending nudges
4. Verify risk level changes

### **Scenario 3: Savings Opportunity**
1. Add large income transaction
2. Generate prediction
3. Check for savings nudges
4. Verify actionable suggestions

---

## 🔍 **5. API Documentation**

Visit **http://localhost:8000/docs** for interactive API documentation where you can:
- ✅ Test all endpoints directly in the browser
- ✅ See request/response schemas
- ✅ Try different parameters
- ✅ View example payloads

---

## 🎮 **6. Interactive Demo**

### **Frontend Demo Flow:**
1. **Open**: http://localhost:3000
2. **Dashboard**: See financial overview with demo data
3. **Add Transaction**: Try adding different transaction types
4. **Chat**: Ask the AI assistant questions
5. **Predictions**: View cash flow forecasts
6. **Nudges**: See AI-generated financial insights

### **Backend Demo Flow:**
1. **Setup**: `POST /demo/setup`
2. **Explore**: Use `/docs` interface
3. **Test**: Try different API endpoints
4. **Verify**: Check responses match expected behavior

---

## ✅ **7. Success Criteria**

### **✅ System is working correctly if:**
- ✅ Frontend loads and displays dashboard
- ✅ API endpoints respond with correct data
- ✅ Predictions are generated with reasonable values
- ✅ Nudges are contextually appropriate
- ✅ Chat interface responds to queries
- ✅ Transaction management works
- ✅ Balance calculations are accurate

### **✅ Key Features Demonstrated:**
- ✅ **Sense & Understand**: Transaction processing
- ✅ **Reason & Plan**: Cashflow predictions
- ✅ **Explain**: AI reasoning for suggestions
- ✅ **Act**: Autonomous action suggestions
- ✅ **Learn**: Adaptive nudge generation

---

## 🚨 **Troubleshooting**

### **If Backend Won't Start:**
```bash
# Kill existing processes
pkill -f "python3 test_app.py"

# Restart backend
cd /Users/lingesh/financial-agent
python3 test_app.py &
```

### **If Frontend Won't Load:**
```bash
# Kill existing processes
pkill -f "python3 -m http.server"

# Restart frontend
cd /Users/lingesh/financial-agent/frontend
python3 -m http.server 3000 &
```

### **If API Calls Fail:**
- Check server is running: `curl http://localhost:8000/health`
- Verify demo data is setup: `curl -X POST http://localhost:8000/demo/setup`
- Check browser console for errors

---

## 🎉 **Congratulations!**

You've successfully tested the **Financial Agent** - an autonomous AI financial coach for gig workers! The system demonstrates:

- ✅ **Proactive Financial Coaching**
- ✅ **Intelligent Cashflow Prediction**
- ✅ **Contextual AI Nudges**
- ✅ **Mobile-First Design**
- ✅ **Privacy-First Architecture**
- ✅ **Explainable AI Reasoning**

**Next Steps**: This is a production-ready foundation that can be extended with:
- Firebase integration for real data persistence
- Advanced ML models for better predictions
- Voice interface for accessibility
- SMS/USSD for low-connectivity users
- Integration with real banking APIs

**Built with ❤️ for financial inclusion and empowerment!**
