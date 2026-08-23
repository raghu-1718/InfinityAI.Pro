export function checkFrontendEnvVars(): string[] {
  const missing: string[] = [];
  const engineA = process.env.NEXT_PUBLIC_ENGINE_A_URL || "https://engine-a-313407263327.asia-south1.run.app";
  const engineB = process.env.NEXT_PUBLIC_ENGINE_B_URL || "https://engine-a-313407263327.asia-south1.run.app";
  const engineC = process.env.NEXT_PUBLIC_ENGINE_C_URL || "https://engine-c-313407263327.asia-south1.run.app";

  if (!engineA) missing.push("NEXT_PUBLIC_ENGINE_A_URL");
  if (!engineB) missing.push("NEXT_PUBLIC_ENGINE_B_URL");
  if (!engineC) missing.push("NEXT_PUBLIC_ENGINE_C_URL");
  return missing;
}
