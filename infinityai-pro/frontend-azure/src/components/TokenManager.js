import React, { useState } from 'react';
import './TokenManager.css';

const TokenManager = ({ onTokenUpdate, onClose, isOpen }) => {
  const [token, setToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationResult, setValidationResult] = useState(null);

  const handleTokenSubmit = async (e) => {
    e.preventDefault();
    
    if (!token.trim()) {
      setError('Please enter a valid access token');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      // Call the parent component's token update function
      await onTokenUpdate(token);
      setValidationResult({
        success: true,
        message: 'Token validated successfully!'
      });
      
      // Close modal after 2 seconds
      setTimeout(() => {
        onClose();
      }, 2000);
      
    } catch (error) {
      setError(error.message || 'Failed to validate access token');
      setValidationResult({
        success: false,
        message: error.message || 'Token validation failed'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDhanOAuth = () => {
    // Redirect to DHAN OAuth flow
    const dhanOAuthUrl = `https://api.dhan.co/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://infinityai-backend-aws.amazonaws.com/api/dhan/callback&state=infinityai_oauth`;
    window.location.href = dhanOAuthUrl;
  };

  if (!isOpen) return null;

  return (
    <div className=\"token-manager-overlay\">
      <div className=\"token-manager-modal\">
        <div className=\"modal-header\">
          <h2>🔑 DHAN Access Token Manager</h2>
          <button className=\"close-button\" onClick={onClose}>×</button>
        </div>
        
        <div className=\"modal-content\">
          <div className="dhan-urls-section">
            <h3>🔗 DHAN API Configuration URLs</h3>
            <div className="url-container">
              <div className="url-item">
                <label>Postback URL:</label>
                <div className="url-box">
                  <code>https://api.infinityai.pro/api/dhan/callback</code>
                  <button className="copy-btn" onClick={() => navigator.clipboard.writeText('https://api.infinityai.pro/api/dhan/callback')}>📋</button>
                </div>
              </div>
              <div className="url-item">
                <label>Redirect URL:</label>
                <div className="url-box">
                  <code>https://infinityai.pro/dashboard</code>
                  <button className="copy-btn" onClick={() => navigator.clipboard.writeText('https://infinityai.pro/dashboard')}>📋</button>
                </div>
              </div>
            </div>
            <p className="url-instructions">
              ℹ️ Copy these URLs and configure them in your DHAN API settings, then request an access token.
            </p>
          </div>

          <div className="token-info">
            <h3>How to get your DHAN Access Token:</h3>
            <ol>
              <li>Log into your DHAN account</li>
              <li>Go to API Management section</li>
              <li>Configure the above URLs in your DHAN API settings</li>
              <li>Generate or copy your Access Token</li>
              <li>Paste it below and click "Update Token"</li>
            </ol>
            <div className="token-warning">
              ⚠️ <strong>Important:</strong> Access tokens expire every 24 hours. You'll need to update it daily.
            </div>
          </div>

          <form onSubmit={handleTokenSubmit} className=\"token-form\">
            <div className=\"form-group\">
              <label htmlFor=\"access-token\">Access Token</label>
              <textarea
                id=\"access-token\"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder=\"Paste your DHAN access token here...\"
                rows={4}
                className=\"token-input\"
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className=\"error-message\">
                <span className=\"error-icon\">❌</span>
                {error}
              </div>
            )}

            {validationResult && (
              <div className={`validation-result ${validationResult.success ? 'success' : 'error'}`}>
                <span className=\"result-icon\">
                  {validationResult.success ? '✅' : '❌'}
                </span>
                {validationResult.message}
              </div>
            )}

            <div className=\"form-actions\">
              <button
                type=\"submit\"
                className=\"btn-primary\"
                disabled={isLoading || !token.trim()}
              >
                {isLoading ? (
                  <>
                    <span className=\"spinner-small\"></span>
                    Validating...
                  </>
                ) : (
                  'Update Token'
                )}
              </button>
              
              <button
                type=\"button\"
                className=\"btn-secondary\"
                onClick={onClose}
                disabled={isLoading}
              >
                Cancel
              </button>
            </div>
          </form>

          <div className=\"oauth-section\">
            <div className=\"divider\">
              <span>OR</span>
            </div>
            
            <button
              type=\"button\"
              className=\"btn-oauth\"
              onClick={handleDhanOAuth}
              disabled={isLoading}
            >
              <span className=\"oauth-icon\">🔐</span>
              Login with DHAN OAuth
            </button>
            
            <p className=\"oauth-description\">
              Use DHAN's secure OAuth flow to automatically generate an access token.
            </p>
          </div>

          <div className=\"security-note\">
            <h4>🔒 Security Information</h4>
            <ul>
              <li>Your access token is stored securely and encrypted</li>
              <li>We never store your DHAN login credentials</li>
              <li>Token is only used to fetch your portfolio and execute trades</li>
              <li>You can revoke access anytime from your DHAN account</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TokenManager;