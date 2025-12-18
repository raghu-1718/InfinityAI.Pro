#!/usr/bin/env node
// Simple Firebase E2E script using Firebase client SDK
// Usage:
// FIREBASE_API_KEY=... FIREBASE_TEST_EMAIL=... FIREBASE_TEST_PASSWORD=... node firebase_e2e.js

import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc } from 'firebase/firestore';

const apiKey = process.env.FIREBASE_API_KEY;
const email = process.env.FIREBASE_TEST_EMAIL;
const password = process.env.FIREBASE_TEST_PASSWORD;

if (!apiKey || !email || !password) {
  console.error('Missing FIREBASE_API_KEY or FIREBASE_TEST_EMAIL or FIREBASE_TEST_PASSWORD');
  process.exit(2);
}

// We need the projectId — try from env or require explicit run with FIREBASE_PROJECT
const projectId = process.env.FIREBASE_PROJECT || undefined;

const firebaseConfig = {
  apiKey,
  authDomain: projectId ? `${projectId}.firebaseapp.com` : undefined,
};

(async () => {
  try {
    const app = initializeApp(firebaseConfig as any);
    const auth = getAuth(app);
    const userCred = await signInWithEmailAndPassword(auth, email, password);
    console.log('Signed in user:', userCred.user.uid);

    const firestore = getFirestore(app);
    const testDocRef = doc(firestore, 'e2e_tests', `run_${Date.now()}`);
    await setDoc(testDocRef, { timestamp: new Date().toISOString(), user: userCred.user.uid });
    console.log('Wrote test document');

    const got = await getDoc(testDocRef);
    console.log('Read back:', got.exists() ? got.data() : 'MISSING');
    console.log('Firebase E2E completed successfully');
  } catch (err) {
    console.error('Firebase e2e failure:', err);
    process.exit(1);
  }
})();
