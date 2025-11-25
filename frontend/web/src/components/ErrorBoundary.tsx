import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('❌ Error caught by boundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-64 flex items-center justify-center bg-red-50 rounded-lg border border-red-200">
          <div className="text-center p-6">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold text-red-800 mb-2">
              Component Error
            </h3>
            <p className="text-red-600 mb-4">
              Something went wrong loading this component.
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: undefined })}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Retry wrapper component
interface RetryProps {
  children: ReactNode;
  maxRetries?: number;
  retryDelay?: number;
}

export const RetryWrapper: React.FC<RetryProps> = ({
  children,
  maxRetries = 3,
  retryDelay = 1000,
}) => {
  const [retryCount, setRetryCount] = React.useState(0);
  const [isRetrying, setIsRetrying] = React.useState(false);

  const handleRetry = () => {
    if (retryCount < maxRetries) {
      setIsRetrying(true);
      setTimeout(() => {
        setRetryCount((prev) => prev + 1);
        setIsRetrying(false);
      }, retryDelay);
    }
  };

  return (
    <ErrorBoundary
      fallback={
        <div className="min-h-32 flex items-center justify-center bg-yellow-50 rounded-lg border border-yellow-200">
          <div className="text-center p-4">
            <div className="text-yellow-500 text-2xl mb-2">🔄</div>
            <p className="text-yellow-700 mb-3">
              {isRetrying ? 'Retrying...' : `Failed to load (${retryCount}/${maxRetries})`}
            </p>
            {retryCount < maxRetries && !isRetrying && (
              <button
                onClick={handleRetry}
                className="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600 transition-colors"
              >
                Retry
              </button>
            )}
          </div>
        </div>
      }
    >
      <div key={retryCount}>{children}</div>
    </ErrorBoundary>
  );
};
