create extension if not exists vector;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  encrypted_identity text,
  created_at timestamptz default now()
);

create table if not exists consumed_transactions (
  tx_hash text primary key,
  sender_wallet text not null,
  court_type text not null,
  amount_gen integer not null,
  consumed_at timestamptz default now()
);

create table if not exists cases (
  id uuid primary key default gen_random_uuid(),
  username text not null,
  country text not null,
  dispute_type text not null,
  court_type text not null,
  status text not null default 'submitted',
  created_at timestamptz default now()
);

create table if not exists evidence_files (
  id uuid primary key default gen_random_uuid(),
  case_id uuid references cases(id),
  bucket text not null,
  object_path text not null,
  mime_type text not null,
  created_at timestamptz default now()
);

create table if not exists legal_chunks (
  id text primary key,
  country text not null,
  category text not null,
  title text not null,
  content text not null,
  importance numeric not null,
  embedding vector(384)
);

create table if not exists verdicts (
  id uuid primary key default gen_random_uuid(),
  case_id uuid references cases(id),
  winner text not null,
  confidence numeric not null,
  verdict_json jsonb not null,
  finalized boolean not null default true,
  created_at timestamptz default now()
);

create table if not exists council_members (
  wallet text primary key,
  voting_weight numeric not null,
  active boolean not null default true
);

create table if not exists council_votes (
  proposal_id text not null,
  wallet text references council_members(wallet),
  vote text not null,
  created_at timestamptz default now(),
  primary key (proposal_id, wallet)
);
