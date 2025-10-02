"""Firebase configuration and initialization."""
import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings
import os


class FirebaseManager:
    """Firebase connection and operations manager."""
    
    def __init__(self):
        self.app = None
        self.db = None
        self.auth = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase connection."""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                self.app = firebase_admin.get_app()
            else:
                # Initialize with service account key or default credentials
                if os.path.exists("firebase-service-account.json"):
                    cred = credentials.Certificate("firebase-service-account.json")
                    self.app = firebase_admin.initialize_app(cred)
                else:
                    # Use default credentials (for production/cloud deployment)
                    self.app = firebase_admin.initialize_app()
            
            # Initialize Firestore database
            self.db = firestore.client(self.app)
            self.auth = auth
            
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            # Fallback to mock for development
            self.db = None
            self.auth = None
    
    def get_database(self):
        """Get Firestore database instance."""
        return self.db
    
    def get_auth(self):
        """Get Firebase Auth instance."""
        return self.auth
    
    def get_collection(self, collection_name: str):
        """Get a Firestore collection reference."""
        if self.db:
            return self.db.collection(collection_name)
        return None


# Global Firebase manager instance
firebase_manager = FirebaseManager()


# Firebase configuration for frontend
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyArm0DzNp3aKXxS7tjFrQ113ms4dVActcw",
    "authDomain": "mumbaihacks-d579f.firebaseapp.com",
    "databaseURL": "https://mumbaihacks-d579f-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "mumbaihacks-d579f",
    "storageBucket": "mumbaihacks-d579f.firebasestorage.app",
    "messagingSenderId": "1017846562337",
    "appId": "1:1017846562337:web:296e5529b1cd78409cad60",
    "measurementId": "G-KNHV768S1M"
}
