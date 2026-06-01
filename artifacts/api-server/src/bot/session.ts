export type DeploymentStep =
  | "idle"
  | "collecting_required"
  | "collecting_optional"
  | "review"
  | "creator_buy"
  | "creator_buy_custom"
  | "target_mcap"
  | "target_mcap_custom"
  | "dex_options"
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

export type Launchpad = "pumpfun" | "raydium";

export interface SessionData {
  step: DeploymentStep;
  collectingField?: string;
  token: TokenConfig;
  withdraw: WithdrawDraft;
  panelTransfer: PanelTransferDraft;
  launchpad?: Launchpad;
  /** SOL the creator buys on launch. 0 = skipped. */
  creatorBuyAmountSol?: number;
  /** USD market cap at which to auto-sell all creator tokens. 0 = disabled. */
  targetMarketCapUsd?: number;
  /** Whether the user opted in to pay for a DEX Screener token info update. */
  dexUpdate?: boolean;
  /** Whether the user opted in to pay for a DEX Screener boost. */
  dexBoost?: boolean;
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
    dexUpdate: false,
    dexBoost: false,
  };
}
