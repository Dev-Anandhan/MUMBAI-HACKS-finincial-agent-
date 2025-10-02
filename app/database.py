"""Firebase database configuration and operations."""
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from app.firebase_config import firebase_manager


class FirebaseDatabase:
    """Firebase database operations manager."""
    
    def __init__(self):
        self.db = firebase_manager.get_database()
    
    def create_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Create a document in Firestore."""
        try:
            if self.db:
                doc_ref = self.db.collection(collection).document(doc_id)
                # Add timestamp
                data['created_at'] = datetime.utcnow().isoformat()
                data['updated_at'] = datetime.utcnow().isoformat()
                doc_ref.set(data)
                return True
            return False
        except Exception as e:
            print(f"Error creating document: {e}")
            return False
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from Firestore."""
        try:
            if self.db:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc = doc_ref.get()
                if doc.exists:
                    return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in Firestore."""
        try:
            if self.db:
                doc_ref = self.db.collection(collection).document(doc_id)
                # Add update timestamp
                data['updated_at'] = datetime.utcnow().isoformat()
                doc_ref.update(data)
                return True
            return False
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document from Firestore."""
        try:
            if self.db:
                doc_ref = self.db.collection(collection).document(doc_id)
                doc_ref.delete()
                return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def query_collection(self, collection: str, filters: List[tuple] = None, 
                        limit: int = None, order_by: str = None) -> List[Dict[str, Any]]:
        """Query a collection with filters."""
        try:
            if not self.db:
                return []
            
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
            
        except Exception as e:
            print(f"Error querying collection: {e}")
            return []
    
    def get_user_documents(self, collection: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a specific user."""
        return self.query_collection(
            collection, 
            filters=[('user_id', '==', user_id)],
            order_by='created_at'
        )


# Global database instance
db = FirebaseDatabase()


def get_database():
    """Dependency to get database instance."""
    return db