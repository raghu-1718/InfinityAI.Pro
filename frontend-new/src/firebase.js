
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU",
  authDomain: "infinity-ai-5ec7c.firebaseapp.com",
  projectId: "infinity-ai-5ec7c",
  storageBucket: "infinity-ai-5ec7c.appspot.com",
  messagingSenderId: "26140490557",
  appId: "1:26140490557:web:6d99cdd77d3f9408c26354",
  measurementId: "G-3GPS2VZQS9"
};


// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Get a Firestore instance
export const db = getFirestore(app);
