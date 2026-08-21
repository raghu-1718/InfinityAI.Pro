"use client";

import { ShadowSignalsLedger } from "@/components/dashboard/shadow-signals-ledger";

export default function SignalsPage() {
  return (
    <div className="container mx-auto p-4 md:p-6 space-y-6 max-w-7xl">
      <ShadowSignalsLedger />
    </div>
  );
}
