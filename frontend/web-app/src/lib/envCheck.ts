export function checkFrontendEnvVars(): string[] {
  const missing: string[] = [];
  const engineA = process.env.NEXT_PUBLIC_ENGINE_A_URL || "https://engine-a-r2f5flt77q-el.a.run.app";
  const engineB = process.env.NEXT_PUBLIC_ENGINE_B_URL || "https://engine-a-r2f5flt77q-el.a.run.app";
  const engineC = process.env.NEXT_PUBLIC_ENGINE_C_URL || "https://engine-c-r2f5flt77q-el.a.run.app";

  if (!engineA) missing.push("NEXT_PUBLIC_ENGINE_A_URL");
  if (!engineB) missing.push("NEXT_PUBLIC_ENGINE_B_URL");
  if (!engineC) missing.push("NEXT_PUBLIC_ENGINE_C_URL");
  return missing;
}
