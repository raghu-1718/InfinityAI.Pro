import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const API_BASE_URL = 'https://api.infinityai.pro'; // Engine D URL

// Async thunks for API calls
export const updateAccessToken = createAsyncThunk(
  'dhan/updateAccessToken',
  async (accessToken, { rejectWithValue }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dhan/token/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ access_token: accessToken }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Token update failed');
      }

      const data = await response.json();
      
      // Store token in localStorage
      localStorage.setItem('dhan_access_token', accessToken);
      localStorage.setItem('dhan_user_info', JSON.stringify(data.user_info));
      
      return {
        accessToken,
        userInfo: data.user_info,
        expiresIn: data.expires_in
      };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchPortfolio = createAsyncThunk(
  'dhan/fetchPortfolio',
  async (_, { getState, rejectWithValue }) => {
    try {
      const accessToken = getState().dhan.accessToken || localStorage.getItem('dhan_access_token');
      
      if (!accessToken) {
        throw new Error('No access token available');
      }

      const response = await fetch(`${API_BASE_URL}/api/portfolio`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Portfolio fetch failed');
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const comprehensiveAnalysis = createAsyncThunk(
  'dhan/comprehensiveAnalysis',
  async (analysisRequest, { getState, rejectWithValue }) => {
    try {
      const accessToken = getState().dhan.accessToken || localStorage.getItem('dhan_access_token');
      
      if (!accessToken) {
        throw new Error('No access token available');
      }

      const response = await fetch(`${API_BASE_URL}/api/analyze/comprehensive`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(analysisRequest),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Analysis failed');
      }

      const data = await response.json();
      return data.analysis;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// Initial state
const initialState = {
  accessToken: localStorage.getItem('dhan_access_token') || null,
  userInfo: JSON.parse(localStorage.getItem('dhan_user_info') || 'null'),
  isTokenValid: !!localStorage.getItem('dhan_access_token'),
  portfolio: null,
  analysis: null,
  loading: false,
  error: null,
  lastUpdated: null,
};

// DHAN slice
const dhanSlice = createSlice({
  name: 'dhan',
  initialState,
  reducers: {
    clearToken: (state) => {
      state.accessToken = null;
      state.userInfo = null;
      state.isTokenValid = false;
      state.portfolio = null;
      state.analysis = null;
      state.error = null;
      localStorage.removeItem('dhan_access_token');
      localStorage.removeItem('dhan_user_info');
    },
    clearError: (state) => {
      state.error = null;
    },
    setTokenExpired: (state) => {
      state.isTokenValid = false;
      state.error = 'Access token has expired. Please update your token.';
    },
  },
  extraReducers: (builder) => {
    // Update Access Token
    builder
      .addCase(updateAccessToken.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateAccessToken.fulfilled, (state, action) => {
        state.loading = false;
        state.accessToken = action.payload.accessToken;
        state.userInfo = action.payload.userInfo;
        state.isTokenValid = true;
        state.error = null;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(updateAccessToken.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.isTokenValid = false;
      })
      
    // Fetch Portfolio
      .addCase(fetchPortfolio.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPortfolio.fulfilled, (state, action) => {
        state.loading = false;
        state.portfolio = action.payload;
        state.error = null;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchPortfolio.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        
        // If unauthorized, mark token as invalid
        if (action.payload?.includes('Unauthorized') || action.payload?.includes('401')) {
          state.isTokenValid = false;
        }
      })
      
    // Comprehensive Analysis
      .addCase(comprehensiveAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(comprehensiveAnalysis.fulfilled, (state, action) => {
        state.loading = false;
        state.analysis = action.payload;
        state.error = null;
      })
      .addCase(comprehensiveAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearToken, clearError, setTokenExpired } = dhanSlice.actions;
export default dhanSlice.reducer;