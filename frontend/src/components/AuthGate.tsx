/**
 * AuthGate Component
 * 
 * Handles user authentication (login and signup)
 * Uses Firebase Authentication with email/password
 */

import { useState, FormEvent } from "react";
import { auth } from "../firebaseConfig";
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword,
  sendPasswordResetEmail,
  AuthError 
} from "firebase/auth";

export default function AuthGate() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);

    try {
      if (isLogin) {
        await signInWithEmailAndPassword(auth, email, password);
        console.log("✅ Login successful");
      } else {
        await createUserWithEmailAndPassword(auth, email, password);
        console.log("✅ Account created successfully");
      }
    } catch (err) {
      const authError = err as AuthError;
      console.error("❌ Authentication error:", authError.code);
      
      // User-friendly error messages
      switch (authError.code) {
        case "auth/email-already-in-use":
          setError("This email is already registered. Please log in.");
          break;
        case "auth/invalid-email":
          setError("Invalid email address.");
          break;
        case "auth/user-not-found":
          setError("No account found with this email.");
          break;
        case "auth/wrong-password":
          setError("Incorrect password.");
          break;
        case "auth/weak-password":
          setError("Password must be at least 6 characters.");
          break;
        case "auth/network-request-failed":
          setError("Network error. Please check your connection.");
          break;
        default:
          setError(authError.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async () => {
    if (!email) {
      setError("Please enter your email address first.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      await sendPasswordResetEmail(auth, email);
      setMessage("Password reset email sent! Check your inbox.");
    } catch (err) {
      const authError = err as AuthError;
      setError("Failed to send reset email: " + authError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>InfinityAI.Pro</h1>
          <p className="tagline">Autonomous Trading Platform</p>
        </div>

        <div className="auth-card">
          <h2>{isLogin ? "Welcome Back" : "Create Account"}</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                disabled={loading}
                minLength={6}
              />
            </div>

            {error && <div className="error-message">{error}</div>}
            {message && <div className="success-message">{message}</div>}

            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? "Processing..." : (isLogin ? "Sign In" : "Create Account")}
            </button>
          </form>

          <div className="auth-footer">
            {isLogin && (
              <button
                type="button"
                onClick={handlePasswordReset}
                className="link-button"
                disabled={loading}
              >
                Forgot Password?
              </button>
            )}
            
            <p>
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              {" "}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError("");
                  setMessage("");
                }}
                className="link-button"
                disabled={loading}
              >
                {isLogin ? "Sign Up" : "Sign In"}
              </button>
            </p>
          </div>
        </div>

        <div className="auth-info">
          <h3>🤖 AI-Powered Trading Features</h3>
          <ul>
            <li>✅ Multi-Strategy Execution (Equities, Options, MCX)</li>
            <li>✅ Real-time Gemini AI Market Analysis</li>
            <li>✅ Automated Portfolio Management</li>
            <li>✅ Secure Dhan API Integration</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
