export type DeploymentStep =
  | "idle"
  | "collecting_required"
  | "collecting_optional"
  | "review"
  | "deploying"
  | "done"
  | "withdraw_address"
  | "withdraw_amount"
  | "withdraw_confirm"
  | "panel_transfer_address"
  | "panel_transfer_amount"
  | "panel_burn_amount";

export interface HistoryEntry {
  step: DeploymentStep;
  collectingField?: string;
}

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

export interface PanelTransferDraft {
  toAddress?: string;
  rawAmount?: bigint;
}

export interface SessionData {
  step: DeploymentStep;
  collectingField?: string;
  token: TokenConfig;
  withdraw: WithdrawDraft;
  panelTransfer: PanelTransferDraft;
  lastMint?: string;
  lastSymbol?: string;
  lastDecimals?: number;
  history: HistoryEntry[];
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
    panelTransfer: {},
    history: [],
  };
}
