// Financial Agent Frontend Application
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, addDoc, getDocs, doc, getDoc } from 'firebase/firestore';
import { getAuth, signInAnonymously, onAuthStateChanged } from 'firebase/auth';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyArm0DzNp3aKXxS7tjFrQ113ms4dVActcw",
  authDomain: "mumbaihacks-d579f.firebaseapp.com",
  databaseURL: "https://mumbaihacks-d579f-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "mumbaihacks-d579f",
  storageBucket: "mumbaihacks-d579f.firebasestorage.app",
  messagingSenderId: "1017846562337",
  appId: "1:1017846562337:web:296e5529b1cd78409cad60",
  measurementId: "G-KNHV768S1M"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const auth = getAuth(app);

// API Base URL (update this to your deployed backend URL)
const API_BASE_URL = 'http://localhost:8000/api/v1';

class FinancialAgent {
    constructor() {
        this.user = null;
        this.currentBalance = 0;
        this.totalSavings = 0;
        this.init();
    }

    async init() {
        // Initialize Firebase Auth
        await this.initializeAuth();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadDashboardData();
        
        // Start chat interface
        this.initializeChat();
    }

    async initializeAuth() {
        try {
            // Sign in anonymously for demo purposes
            const userCredential = await signInAnonymously(auth);
            this.user = userCredential.user;
            console.log('User signed in:', this.user.uid);
        } catch (error) {
            console.error('Auth error:', error);
        }
    }

    setupEventListeners() {
        // Add transaction modal
        const addTransactionBtn = document.getElementById('addTransactionBtn');
        const transactionModal = document.getElementById('transactionModal');
        const closeModal = document.getElementById('closeModal');
        const transactionForm = document.getElementById('transactionForm');

        addTransactionBtn.addEventListener('click', () => {
            transactionModal.classList.remove('hidden');
            transactionModal.classList.add('flex');
        });

        closeModal.addEventListener('click', () => {
            transactionModal.classList.add('hidden');
            transactionModal.classList.remove('flex');
        });

        transactionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTransaction();
        });

        // Quick action buttons
        document.getElementById('viewSavingsBtn').addEventListener('click', () => {
            this.showSavingsPots();
        });

        document.getElementById('predictionsBtn').addEventListener('click', () => {
            this.showPredictions();
        });

        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettings();
        });

        // Chat interface
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');

        sendBtn.addEventListener('click', () => {
            this.sendChatMessage();
        });

        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });
    }

    async loadDashboardData() {
        try {
            // Simulate API calls to backend
            // In a real implementation, these would be actual API calls
            
            // Load user profile
            await this.loadUserProfile();
            
            // Load transactions
            await this.loadTransactions();
            
            // Load predictions
            await this.loadPredictions();
            
            // Load nudges
            await this.loadNudges();
            
            // Update UI
            this.updateDashboard();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadUserProfile() {
        // Mock user profile data
        this.userProfile = {
            name: "Demo User",
            phone: "+1234567890",
            income_schedule: "irregular",
            risk_tolerance: "conservative",
            auto_actions_enabled: true
        };
    }

    async loadTransactions() {
        // Mock transaction data
        this.transactions = [
            {
                id: 1,
                amount: 5000,
                type: "income",
                category: "gig_income",
                description: "Freelance project payment",
                date: new Date().toISOString()
            },
            {
                id: 2,
                amount: -1200,
                type: "expense",
                category: "groceries",
                description: "Weekly groceries",
                date: new Date(Date.now() - 86400000).toISOString()
            },
            {
                id: 3,
                amount: -300,
                type: "expense",
                category: "transport",
                description: "Uber rides",
                date: new Date(Date.now() - 172800000).toISOString()
            }
        ];

        // Calculate current balance
        this.currentBalance = this.transactions.reduce((sum, t) => sum + t.amount, 0);
    }

    async loadPredictions() {
        // Mock prediction data
        this.prediction = {
            predicted_balance: this.currentBalance - 500,
            shortfall_probability: 0.3,
            confidence_level: 0.8,
            reasoning: "Based on your spending patterns, you might face a small shortfall in 5 days. Consider reducing discretionary spending."
        };
    }

    async loadNudges() {
        // Mock nudges data
        this.nudges = [
            {
                id: 1,
                title: "Savings Opportunity",
                message: "You have ₹2000 extra this month. Consider saving ₹500 to your emergency fund.",
                type: "actionable",
                priority: "medium",
                suggested_action: {
                    type: "save_to_emergency",
                    amount: 500
                }
            },
            {
                id: 2,
                title: "Spending Alert",
                message: "Your entertainment spending is 40% higher this week. Consider reducing it.",
                type: "informational",
                priority: "low"
            }
        ];
    }

    updateDashboard() {
        // Update balance display
        document.getElementById('currentBalance').textContent = `₹${this.currentBalance.toLocaleString()}`;
        
        // Update savings (mock data)
        this.totalSavings = 15000;
        document.getElementById('savings').textContent = `₹${this.totalSavings.toLocaleString()}`;
        
        // Update risk level
        const riskLevel = this.prediction.shortfall_probability > 0.6 ? 'High' : 
                         this.prediction.shortfall_probability > 0.3 ? 'Medium' : 'Low';
        document.getElementById('riskLevel').textContent = riskLevel;
        
        // Update risk bar color and width
        const riskBar = document.getElementById('riskBar');
        const riskPercentage = this.prediction.shortfall_probability * 100;
        riskBar.style.width = `${riskPercentage}%`;
        
        if (riskPercentage > 60) {
            riskBar.className = 'bg-red-500 h-2 rounded-full';
        } else if (riskPercentage > 30) {
            riskBar.className = 'bg-yellow-500 h-2 rounded-full';
        } else {
            riskBar.className = 'bg-green-500 h-2 rounded-full';
        }
        
        // Update forecast message
        document.getElementById('forecastMessage').textContent = this.prediction.reasoning;
        
        // Update nudges
        this.updateNudges();
    }

    updateNudges() {
        const nudgesList = document.getElementById('nudgesList');
        
        if (this.nudges.length === 0) {
            nudgesList.innerHTML = '<div class="text-gray-500 text-sm">No active insights at the moment.</div>';
            return;
        }
        
        nudgesList.innerHTML = this.nudges.map(nudge => `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                <div class="font-medium text-blue-800 mb-1">${nudge.title}</div>
                <div class="text-sm text-blue-700 mb-2">${nudge.message}</div>
                ${nudge.suggested_action ? `
                    <button onclick="financialAgent.actOnNudge('${nudge.id}')" 
                            class="bg-blue-500 text-white text-xs px-3 py-1 rounded hover:bg-blue-600 transition-colors">
                        ${nudge.suggested_action.type === 'save_to_emergency' ? 'Save ₹' + nudge.suggested_action.amount : 'Take Action'}
                    </button>
                ` : ''}
            </div>
        `).join('');
    }

    async addTransaction() {
        const form = document.getElementById('transactionForm');
        const formData = new FormData(form);
        
        const transaction = {
            amount: parseFloat(document.getElementById('amount').value),
            transaction_type: document.getElementById('transactionType').value,
            category: document.getElementById('category').value,
            description: document.getElementById('description').value,
            transaction_date: new Date().toISOString(),
            source_type: 'manual'
        };
        
        // Make amount negative for expenses
        if (transaction.transaction_type === 'expense') {
            transaction.amount = -transaction.amount;
        }
        
        try {
            // In a real implementation, this would be an API call
            console.log('Adding transaction:', transaction);
            
            // Add to local array for demo
            this.transactions.push({
                id: Date.now(),
                ...transaction
            });
            
            // Recalculate balance
            this.currentBalance = this.transactions.reduce((sum, t) => sum + t.amount, 0);
            
            // Update UI
            this.updateDashboard();
            
            // Close modal
            document.getElementById('transactionModal').classList.add('hidden');
            document.getElementById('transactionModal').classList.remove('flex');
            
            // Reset form
            form.reset();
            
            // Show success message
            this.showSuccess('Transaction added successfully!');
            
        } catch (error) {
            console.error('Error adding transaction:', error);
            this.showError('Failed to add transaction');
        }
    }

    actOnNudge(nudgeId) {
        const nudge = this.nudges.find(n => n.id == nudgeId);
        if (!nudge || !nudge.suggested_action) return;
        
        if (nudge.suggested_action.type === 'save_to_emergency') {
            this.showSavingsPots();
        }
        
        // Remove nudge from list after action
        this.nudges = this.nudges.filter(n => n.id != nudgeId);
        this.updateNudges();
        
        this.showSuccess('Action taken successfully!');
    }

    showSavingsPots() {
        alert('Savings Pots feature coming soon! This would show your savings goals and allow you to contribute to them.');
    }

    showPredictions() {
        alert('Detailed Predictions feature coming soon! This would show your cash flow forecast and risk analysis.');
    }

    showSettings() {
        alert('Settings feature coming soon! This would allow you to configure your preferences and connect accounts.');
    }

    initializeChat() {
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
    }

    sendChatMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        
        // Clear input
        this.chatInput.value = '';
        
        // Generate AI response
        setTimeout(() => {
            const response = this.generateAIResponse(message);
            this.addChatMessage(response, 'ai');
        }, 1000);
    }

    addChatMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-bubble';
        
        const isUser = sender === 'user';
        const bgColor = isUser ? 'bg-green-100' : 'bg-blue-100';
        const icon = isUser ? 'fas fa-user' : 'fas fa-robot';
        const iconColor = isUser ? 'text-green-500' : 'text-blue-500';
        
        messageDiv.innerHTML = `
            <div class="${bgColor} p-3 rounded-lg">
                <div class="flex items-start space-x-2">
                    <i class="${icon} ${iconColor} mt-1"></i>
                    <div>
                        <div class="text-sm text-gray-800">${message}</div>
                        <div class="text-xs text-gray-500 mt-1">${new Date().toLocaleTimeString()}</div>
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    generateAIResponse(userMessage) {
        const message = userMessage.toLowerCase();
        
        if (message.includes('balance') || message.includes('money')) {
            return `Your current balance is ₹${this.currentBalance.toLocaleString()}. Based on your spending patterns, I predict you might have ₹${(this.currentBalance - 500).toLocaleString()} in 7 days.`;
        }
        
        if (message.includes('save') || message.includes('saving')) {
            return `You currently have ₹${this.totalSavings.toLocaleString()} in savings. I recommend setting aside ₹500 this month for your emergency fund. Would you like me to help you set up automatic savings?`;
        }
        
        if (message.includes('spend') || message.includes('expense')) {
            return `Your spending this month looks good! Your biggest expense categories are groceries and transport. Consider reducing entertainment spending by 20% to improve your savings.`;
        }
        
        if (message.includes('predict') || message.includes('forecast')) {
            return `Based on your transaction history, I predict a ${this.prediction.shortfall_probability > 0.5 ? 'potential shortfall' : 'stable cash flow'} in the next 7 days. ${this.prediction.reasoning}`;
        }
        
        if (message.includes('help') || message.includes('advice')) {
            return `I can help you with: 1) Tracking your expenses, 2) Predicting cash flow, 3) Suggesting savings strategies, 4) Setting up automatic actions. What would you like to know more about?`;
        }
        
        // Default response
        return `I understand you're asking about "${userMessage}". I'm here to help with your financial planning. You can ask me about your balance, spending patterns, savings goals, or cash flow predictions.`;
    }

    showSuccess(message) {
        // Simple success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showError(message) {
        // Simple error notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize the application
const financialAgent = new FinancialAgent();
