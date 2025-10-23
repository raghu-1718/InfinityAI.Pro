import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  projectId: "infinity-ai-5ec7c",
  appId: "1:26140490557:web:6d99cdd77d3f9408c26354",
  storageBucket: "infinity-ai-5ec7c.appspot.com",
  apiKey: "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU",
  authDomain: "infinity-ai-5ec7c.firebaseapp.com",
  messagingSenderId: "26140490557",
  measurementId: "G-3GPS2VZQS9"
};

// Initialize Firebase
//This is a test comment to trigger the CI/CD pipeline
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
