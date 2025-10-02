// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "firebase/firestore";
import { getAuth } from "firebase/auth";
import { getDatabase } from "firebase/database";

// Your web app's Firebase configuration
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

// Initialize Firebase services
export const analytics = getAnalytics(app);
export const db = getFirestore(app);
export const auth = getAuth(app);
export const realtimeDb = getDatabase(app);

export default app;
