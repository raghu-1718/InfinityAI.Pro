// src/components/DhanConnectPrompt.tsx
'use client';
import React from 'react';
import { Button } from '@/components/ui/button';

export function DhanConnectPrompt({ onConnect }: { onConnect?: () => void }) {
  return (
    <div className="bg-yellow-100 border border-yellow-400 text-yellow-900 p-4 rounded mb-4 flex flex-col items-center">
      <div className="font-bold mb-2">Dhan Account Not Connected</div>
      <div className="mb-2">You must connect your Dhan account to enable trading and portfolio features.</div>
      <Button onClick={onConnect} variant="outline" className="bg-yellow-300 hover:bg-yellow-400 text-yellow-900 font-bold">Connect Dhan</Button>
    </div>
  );
}
