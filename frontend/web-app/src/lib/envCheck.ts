const REQUIRED_FRONTEND_ENV_VARS = [
  "NEXT_PUBLIC_ENGINE_A_URL",
  "NEXT_PUBLIC_ENGINE_B_URL",
  "NEXT_PUBLIC_ENGINE_C_URL",
] as const;

export function checkFrontendEnvVars(): string[] {
  return REQUIRED_FRONTEND_ENV_VARS.filter((key) => !process.env[key]);
}
