export type DeploymentStep =
  | "idle"
  | "collecting_required"
  | "collecting_optional"
  | "review"
  | "deploying"
  | "done";

export interface TokenConfig {
  name?: string;
  symbol?: string;
  supply?: number;
  decimals?: number;
  description?: string;
  logoUrl?: string;
  website?: string;
  telegram?: string;
  twitter?: string;
  revokeMint?: boolean;
  revokeFreeze?: boolean;
}

export interface SessionData {
  step: DeploymentStep;
  collectingField?: string;
  token: TokenConfig;
  deploymentFee?: number;
  lastMessageId?: number;
}

export function defaultSession(): SessionData {
  return {
    step: "idle",
    token: {
      decimals: 9,
      revokeMint: false,
      revokeFreeze: false,
    },
  };
}
