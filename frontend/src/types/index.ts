/**
 * Canonical types synchronized with Backend Pydantic Schemas.
 */

export type PolicyDecisionEnum = 'ALLOW' | 'BLOCK' | 'QUARANTINE' | 'REVIEW';

export type TrustLabel =
  | 'trusted_policy'
  | 'user_input'
  | 'untrusted_external'
  | 'agent_generated'
  | 'tool_result'
  | 'validated';

export type AgentRole = 'backend' | 'db_manager' | 'qa' | 'devops' | 'custom';

export type AgentStatus =
  | 'idle'
  | 'running'
  | 'completed'
  | 'blocked'
  | 'quarantined'
  | 'failed'
  | 'review_required';

export interface AgentNodeConfig {
  node_id: string;
  name: string;
  role: AgentRole;
  model: string;
  instructions: string;
  allowed_peers: string[];
  allowed_tools: string[];
  timeout_seconds: number;
  call_limit: number;
  metadata?: Record<string, any>;
}

export interface WorkflowEdge {
  source_node_id: string;
  target_node_id: string;
  metadata?: Record<string, any>;
}

export interface WorkflowConfig {
  workflow_id: string;
  name: string;
  version: string;
  description: string;
  entry_node_id: string;
  nodes: AgentNodeConfig[];
  edges: WorkflowEdge[];
  metadata?: Record<string, any>;
}

export interface AuditEvent {
  event_id: string;
  run_id: string;
  trace_id: string;
  parent_event_id?: string | null;
  timestamp: string;
  actor_id: string;
  target_id?: string | null;
  event_type: string;
  policy_decision?: PolicyDecisionEnum | null;
  reason_code?: string | null;
  policy_version?: string | null;
  duration_ms?: number | null;
  trust_labels: TrustLabel[];
  safe_payload_summary?: string | null;
  payload_metadata?: Record<string, any>;
}

export interface MetricResult {
  name: string;
  version: string;
  value?: number | null;
  available: boolean;
  unavailable_reason?: string | null;
  numerator?: number | null;
  denominator?: number | null;
  metadata?: Record<string, any>;
}

export interface RunMetrics {
  run_id: string;
  css: MetricResult;
  tue: MetricResult;
  task_success: boolean;
  security_blocked_attacks: number;
  total_messages: number;
  total_tool_calls: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
}
