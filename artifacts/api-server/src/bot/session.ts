export type DeploymentStep =
  | "idle"
  | "collecting_required"
  | "collecting_optional"
  | "review"
  | "deploying"
  | "done"
  | "withdraw_address"
  | "withdraw_amount"
  | "withdraw_confirm";

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

export interface WithdrawDraft {
  toAddress?: string;
  amount?: number;
}

export interface SessionData {
  step: DeploymentStep;
  collectingField?: string;
  token: TokenConfig;
  withdraw: WithdrawDraft;
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
    withdraw: {},
  };
}
