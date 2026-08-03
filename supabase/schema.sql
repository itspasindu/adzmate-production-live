-- Optional: run in Supabase SQL editor if you also want workspaces in Supabase Postgres.
-- AdzMate stores workspaces in the API database by default; Supabase is used for Auth (JWT).

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'approver', 'member', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;

create policy "members can read workspaces"
  on public.workspaces for select
  using (
    exists (
      select 1 from public.workspace_members m
      where m.workspace_id = workspaces.id and m.user_id = auth.uid()
    )
  );

create policy "members can read memberships"
  on public.workspace_members for select
  using (user_id = auth.uid() or exists (
    select 1 from public.workspace_members m
    where m.workspace_id = workspace_members.workspace_id and m.user_id = auth.uid()
  ));
