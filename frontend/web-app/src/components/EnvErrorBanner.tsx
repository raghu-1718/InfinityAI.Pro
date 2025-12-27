// src/components/EnvErrorBanner.tsx
'use client';
import React from 'react';

export function EnvErrorBanner({ missing }: { missing: string[] }) {
  if (!missing.length) return null;
  return (
    <div className="bg-red-900 text-red-100 p-4 text-center z-50">
      <strong>Critical Error:</strong> The following environment variables are missing or invalid:<br />
      <span className="font-mono text-xs">{missing.join(', ')}</span><br />
      The app cannot function until these are set with real, production values.
    </div>
  );
}
