/**
 * CredentialsForm Component
 * 
 * Allows users to save their Dhan API credentials securely
 * Displays redirect and postback URLs for Dhan broker configuration
 * Real URLs for infinity-ai-5ec7c project
 */

import { useState, FormEvent } from "react";
import { httpsCallable, HttpsCallableResult } from "firebase/functions";
import { functions } from "../firebaseConfig";
import { User } from "firebase/auth";

interface CredentialsFormProps {
  user: User;
}

interface SaveCredentialsData {
  userId: string;
  clientId: string;
  apiKey: string;
  apiSecret: string;
  accessToken?: string;
}

interface SaveCredentialsResponse {
  message: string;
  status?: string;
}

export default function CredentialsForm({ user }: CredentialsFormProps) {
  const [clientId, setClientId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Real URLs for infinity-ai-5ec7c project
  const REDIRECT_URL = "https://infinity-ai-5ec7c.web.app/auth/dhan/callback";
  const POSTBACK_URL = "https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/submitDhanCredentialsV2";

  const handleSaveCredentials = async (e: FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const saveFn = httpsCallable<SaveCredentialsData, SaveCredentialsResponse>(
        functions,
        "submitDhanCredentialsV2"
      );

      const result: HttpsCallableResult<SaveCredentialsResponse> = await saveFn({
        userId: user.uid,
        clientId,
        apiKey,
        apiSecret,
        accessToken: accessToken || undefined,
      });

      setMessage(result.data.message || "Credentials saved successfully!");
      console.log("✅ Credentials saved:", result.data);

      // Clear sensitive fields after successful save
      setTimeout(() => {
        setMessage("");
      }, 5000);
    } catch (err: any) {
      console.error("❌ Failed to save credentials:", err);
      setError(err.message || "Failed to save credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setMessage(`${label} copied to clipboard!`);
    setTimeout(() => setMessage(""), 3000);
  };

  return (
    <div className="credentials-container">
      <div className="credentials-card">
        <h3>🔐 Dhan API Credentials</h3>
        <p className="description">
          Enter your Dhan broker API credentials to enable automated trading.
          All data is encrypted and stored securely.
        </p>

        <form onSubmit={handleSaveCredentials}>
          <div className="form-group">
            <label htmlFor="clientId">Client ID</label>
            <input
              id="clientId"
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="Enter your Dhan Client ID"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="apiKey">API Key</label>
            <input
              id="apiKey"
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your Dhan API Key"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="apiSecret">API Secret</label>
            <input
              id="apiSecret"
              type="password"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              placeholder="Enter your Dhan API Secret"
              required
              disabled={loading}
            />
            <small>⚠️ Keep this secret safe. Never share it with anyone.</small>
          </div>

          <div className="form-group">
            <label htmlFor="accessToken">Access Token (Optional)</label>
            <input
              id="accessToken"
              type="text"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              placeholder="Enter access token (if you have one)"
              disabled={loading}
            />
            <small>Leave empty if you haven't generated a token yet</small>
          </div>

          {error && <div className="error-message">{error}</div>}
          {message && <div className="success-message">{message}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Saving..." : "💾 Save Credentials"}
          </button>
        </form>
      </div>

      <div className="urls-card">
        <h3>🔗 Configuration URLs</h3>
        <p className="description">
          Use these URLs when setting up your Dhan API integration in the Dhan broker portal.
        </p>

        <div className="url-group">
          <label>Redirect URL</label>
          <div className="url-container">
            <code>{REDIRECT_URL}</code>
            <button
              type="button"
              className="btn-copy"
              onClick={() => copyToClipboard(REDIRECT_URL, "Redirect URL")}
            >
              📋 Copy
            </button>
          </div>
          <small>Configure this in Dhan API settings as the OAuth redirect URL</small>
        </div>

        <div className="url-group">
          <label>Postback URL</label>
          <div className="url-container">
            <code>{POSTBACK_URL}</code>
            <button
              type="button"
              className="btn-copy"
              onClick={() => copyToClipboard(POSTBACK_URL, "Postback URL")}
            >
              📋 Copy
            </button>
          </div>
          <small>Configure this in Dhan API settings for order status updates</small>
        </div>
      </div>

      <div className="credentials-help">
        <h4>📖 How to Get Dhan API Credentials</h4>
        <ol>
          <li>Log in to your Dhan broker account</li>
          <li>Navigate to API Settings / Developer Console</li>
          <li>Generate new API credentials (Client ID, API Key, API Secret)</li>
          <li>Configure the Redirect URL and Postback URL above</li>
          <li>Copy and paste your credentials into this form</li>
          <li>Click "Save Credentials" to store them securely</li>
        </ol>

        <div className="security-note">
          🔒 <strong>Security:</strong> Your credentials are encrypted using AES-256-GCM
          before being stored in Firestore. Only you can access them.
        </div>
      </div>
    </div>
  );
}
