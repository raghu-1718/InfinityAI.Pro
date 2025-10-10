import React, { useMemo, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Alert,
  Box,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  IconButton,
  Tooltip
} from '@mui/material';
import { ContentCopy } from '@mui/icons-material';

const LoginDialog = ({ open, onClose, apiUrl, onSuccess }) => {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { redirectUrl, postbackUrl } = useMemo(() => {
    try {
      const base = new URL(apiUrl);
      const protocol = base.protocol; // keep current scheme (http/https)
      const host = base.host;
      const basePath = base.pathname.endsWith('/') ? base.pathname.slice(0, -1) : base.pathname;
      const engineCPath = basePath.replace(/\/engine-d$/, '') + '/engine-c';
      return {
        redirectUrl: `${protocol}//${host}${engineCPath}/auth/dhan/callback`,
        postbackUrl: `${protocol}//${host}${engineCPath}/webhooks/dhan/postback`
      };
    } catch (_) {
      // Fallback to current location
      const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
      const protocol = isHttps ? 'https:' : 'http:';
      const host = typeof window !== 'undefined' ? window.location.host : 'localhost';
      return {
        redirectUrl: `${protocol}//${host}/engine-c/auth/dhan/callback`,
        postbackUrl: `${protocol}//${host}/engine-c/webhooks/dhan/postback`
      };
    }
  }, [apiUrl]);

  const copy = async (text) => {
    try { await navigator.clipboard.writeText(text); } catch (_) {}
  };

  const handleLogin = async () => {
    setError('');
    setLoading(true);
    try {
      // Store token temporarily for validation
      if (remember) {
        localStorage.setItem('token', token);
      } else {
        sessionStorage.setItem('token', token);
      }

      // Validate identity if endpoint exists
      try {
        const resp = await fetch(`${apiUrl}/user/me`, {
          credentials: 'include',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (resp.ok) {
          const me = await resp.json();
          onSuccess({ token, user: me });
          onClose();
          setLoading(false);
          return;
        }
      } catch (_) {
        // non-blocking; continue
      }

      // If /user/me not available, accept token and let app proceed
      onSuccess({ token, user: null });
      onClose();
    } catch (e) {
      setError('Login failed. Please check your token and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Sign In</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        )}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="API Token"
            type="password"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste your API token"
            fullWidth
          />
          <FormControlLabel
            control={<Checkbox checked={remember} onChange={(e) => setRemember(e.target.checked)} />}
            label="Remember me on this device"
          />
          {/* Dhan Connect URLs */}
          <TextField
            label="Dhan Redirect URL"
            value={redirectUrl}
            fullWidth
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip title="Copy">
                    <IconButton onClick={() => copy(redirectUrl)} size="small">
                      <ContentCopy fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              )
            }}
          />
          <TextField
            label="Dhan Postback URL"
            value={postbackUrl}
            fullWidth
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip title="Copy">
                    <IconButton onClick={() => copy(postbackUrl)} size="small">
                      <ContentCopy fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              )
            }}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleLogin} variant="contained" disabled={loading || !token.trim()}>
          {loading ? 'Signing in…' : 'Sign In'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LoginDialog;
