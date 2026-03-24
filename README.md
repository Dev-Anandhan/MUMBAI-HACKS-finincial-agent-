# Financial Agent - Autonomous AI Financial Coach

An autonomous, privacy-first financial coaching agent designed specifically for gig workers, informal sector employees, and everyday citizens with irregular income patterns. The agent learns each user's financial behavior and proactively plans, nudges, and takes low-risk actions to improve short-term resilience and long-term financial wellbeing.

## 🌟 Key Features

### Core Capabilities
- **Probabilistic Cashflow Prediction**: Uses ML models to predict shortfalls before they happen
- **Autonomous Actions**: Takes low-risk micro-actions (savings, bill reminders, subscription management)
- **Explainable AI**: Provides clear reasoning for every suggestion and action
- **Personalized Nudges**: Context-aware financial coaching based on individual patterns
- **Privacy-First**: Local processing where possible, minimal data retention

### Target Users
- Gig workers with irregular income
- Informal sector employees
- Freelancers and contractors
- Anyone with variable cash flow

## 🏗️ Architecture

### Backend (FastAPI + Firebase)
- **API Layer**: RESTful APIs with comprehensive endpoints
- **ML Services**: Cashflow prediction, anomaly detection, decision engine
- **Database**: Firebase Firestore for scalable, real-time data
- **Authentication**: Firebase Auth with JWT tokens
- **Privacy**: Encrypted data storage, minimal retention policies

### Frontend (Progressive Web App)
- **Mobile-First**: Responsive design optimized for mobile devices
- **Offline Capable**: Works with limited connectivity
- **Voice Support**: Voice-first mode for low-literacy users
- **Multi-Language**: Support for local languages

### Core Services
1. **Cashflow Predictor**: Time-series analysis for income/expense forecasting
2. **Nudge Engine**: Intelligent financial coaching with contextual suggestions
3. **Decision Engine**: Rule-based safety layer with ML-powered recommendations
4. **Transaction Service**: Smart categorization and pattern recognition
5. **Savings Pot Service**: Goal-based savings management

## 🚀 Quick Start

### Prerequisites
- Python 3.13 // chnaged the depencey for upgrade 
- Node.js 16+
- Firebase project setup

### Backend Setup

1. **Clone and Install Dependencies**
```bash
cd financial-agent
pip install -r requirements.txt
```

2. **Configure Firebase**
```bash
# Create Firebase service account key
# Download and place as firebase-service-account.json
```

3. **Set Environment Variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Run the Backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to Frontend Directory**
```bash
cd frontend
```

2. **Open in Browser**
```bash
# Simply open index.html in a modern browser
# Or serve with a local server:
python -m http.server 3000
```

3. **Access the Application**
- Backend API: http://localhost:8000
- Frontend App: http://localhost:3000
- API Documentation: http://localhost:8000/docs

## 📱 User Experience

### Onboarding Flow
1. **Quick Profile Setup**: Income schedule, goals, risk tolerance
2. **Transaction Import**: Connect accounts or manual entry
3. **AI Learning**: System learns patterns from transaction history
4. **Personalized Coaching**: Active nudges and suggestions begin

### Daily Interactions
- **Proactive Alerts**: "Predicted shortfall in 3 days - save ₹300 now?"
- **Smart Actions**: Auto-save to emergency fund when balance is high
- **Contextual Advice**: "Your entertainment spending is 40% higher this week"
- **Voice Commands**: "How much can I spend today?"

### Autonomous Actions (Opt-in)
- **Micro-Savings**: Automatic ₹100-500 transfers to emergency fund
- **Subscription Management**: Pause non-essential services during low cash flow
- **Bill Scheduling**: Advance payment reminders based on income patterns
- **Spending Limits**: Temporary restrictions during predicted shortfalls

## 🔧 API Endpoints

### Core Endpoints
- `POST /api/v1/users/` - Create user profile
- `GET /api/v1/transactions/` - Get transaction history
- `POST /api/v1/predictions/` - Generate cashflow prediction
- `GET /api/v1/nudges/` - Get financial nudges
- `POST /api/v1/actions/` - Create autonomous action
- `GET /api/v1/pots/` - Get savings pots

### Authentication
All endpoints require JWT authentication via Firebase Auth.

## 🛡️ Privacy & Security

### Privacy-First Design
- **Local Processing**: Balance checks and basic rules on-device
- **Minimal Data**: Only essential features stored centrally
- **User Control**: Granular permissions for data sources and actions
- **Data Retention**: Automatic deletion after configured period

### Security Measures
- **Encryption**: All data encrypted at rest and in transit
- **Access Control**: Role-based permissions and audit trails
- **Rate Limiting**: Protection against abuse
- **Regular Audits**: Security reviews and penetration testing

## 🎯 Success Metrics

### User-Centered Metrics
- **Reduction in Shortfalls**: % fewer days with balance < threshold
- **Emergency Fund Growth**: Increase in days of expenses saved
- **Action Engagement**: % of suggested actions accepted
- **User Retention**: Monthly active users

### Safety Metrics
- **Action Reversal Rate**: % of automated actions undone
- **User Satisfaction**: Trust and satisfaction scores
- **Error Rate**: Failed predictions and actions

## 🔮 Future Roadmap

### Phase 1 (Months 1-3): MVP
- ✅ Core prediction engine
- ✅ Basic nudge system
- ✅ Simple autonomous actions
- ✅ Mobile web interface

### Phase 2 (Months 4-6): Enhanced Features
- 🔄 Voice bot integration
- 🔄 SMS/USSD support
- 🔄 Advanced ML models
- 🔄 Multi-language support

### Phase 3 (Months 7-12): Scale & Optimize
- 🔄 Federated learning
- 🔄 Marketplace integrations
- 🔄 Advanced analytics
- 🔄 Regulatory compliance

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and code of conduct.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for the Mumbai Hacks 2024 hackathon
- Inspired by the financial challenges faced by gig workers globally
- Thanks to the open-source community for the amazing tools and libraries

## 📞 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues
- **Email**: support@financialagent.ai

---

**Built with ❤️ for financial inclusion and empowerment**
