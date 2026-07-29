"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { WorkspaceShell } from "@/components/workspace-shell";
import type {
  AccessPermission,
  AccessRole,
  AccessUser,
  AdminHotel,
  PaginatedResponse,
  RoleListResponse,
} from "@/lib/types";

const API_PREFIX = process.env.NEXT_PUBLIC_BASE_PATH || "";

type UserFormState = {
  id: string | null;
  email: string;
  full_name: string;
  password: string;
  is_active: boolean;
  role_codes: string[];
  hotel_ids: string[];
};

type RoleFormState = {
  id: string | null;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
  permission_codes: string[];
};

const EMPTY_USER_FORM: UserFormState = {
  id: null,
  email: "",
  full_name: "",
  password: "",
  is_active: true,
  role_codes: [],
  hotel_ids: [],
};

const EMPTY_ROLE_FORM: RoleFormState = {
  id: null,
  code: "",
  name: "",
  description: "",
  is_active: true,
  permission_codes: [],
};

function roleCodesFromUser(user: AccessUser) {
  return user.roles.map((role) => role.code);
}

function userFormFromUser(user: AccessUser): UserFormState {
  return {
    id: user.id,
    email: user.email,
    full_name: user.full_name,
    password: "",
    is_active: user.is_active,
    role_codes: roleCodesFromUser(user),
    hotel_ids: user.hotel_ids,
  };
}

function roleFormFromRole(role: AccessRole): RoleFormState {
  return {
    id: role.id,
    code: role.code,
    name: role.name,
    description: role.description ?? "",
    is_active: role.is_active,
    permission_codes: role.permissions.map((permission) => permission.code),
  };
}

export function AdminUserRoleManager() {
  const [users, setUsers] = useState<AccessUser[]>([]);
  const [roles, setRoles] = useState<AccessRole[]>([]);
  const [permissions, setPermissions] = useState<AccessPermission[]>([]);
  const [hotels, setHotels] = useState<AdminHotel[]>([]);
  const [userForm, setUserForm] = useState<UserFormState>(EMPTY_USER_FORM);
  const [roleForm, setRoleForm] = useState<RoleFormState>(EMPTY_ROLE_FORM);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isPending, startTransition] = useTransition();

  async function readJsonOrThrow(response: Response, fallbackMessage: string) {
    const raw = await response.text();
    let parsed: unknown = null;

    try {
      parsed = raw ? JSON.parse(raw) : null;
    } catch {
      parsed = null;
    }

    if (!response.ok) {
      const detail =
        parsed && typeof parsed === "object" && "detail" in parsed
          ? String((parsed as { detail?: unknown }).detail ?? fallbackMessage)
          : raw || fallbackMessage;
      throw new Error(detail);
    }

    return parsed;
  }

  async function loadAll() {
    const [usersResponse, rolesResponse, permissionsResponse, hotelsResponse] = await Promise.all([
      fetch(`${API_PREFIX}/api/admin/users?limit=200&offset=0`, { cache: "no-store" }),
      fetch(`${API_PREFIX}/api/admin/roles`, { cache: "no-store" }),
      fetch(`${API_PREFIX}/api/admin/permissions`, { cache: "no-store" }),
      fetch(`${API_PREFIX}/api/hotels?limit=200&offset=0`, { cache: "no-store" }),
    ]);

    const usersPayload = (await readJsonOrThrow(
      usersResponse,
      "Failed to load users",
    )) as Partial<PaginatedResponse<AccessUser>>;
    const rolesPayload = (await readJsonOrThrow(
      rolesResponse,
      "Failed to load roles",
    )) as Partial<RoleListResponse>;
    const permissionsPayload = (await readJsonOrThrow(
      permissionsResponse,
      "Failed to load permissions",
    )) as AccessPermission[] | { items?: AccessPermission[] };
    const hotelsPayload = (await readJsonOrThrow(
      hotelsResponse,
      "Failed to load hotels",
    )) as Partial<PaginatedResponse<AdminHotel>>;

    setUsers(Array.isArray(usersPayload.items) ? usersPayload.items : []);
    setRoles(Array.isArray(rolesPayload.items) ? rolesPayload.items : []);
    setPermissions(
      Array.isArray(permissionsPayload)
        ? permissionsPayload
        : Array.isArray(permissionsPayload.items)
          ? permissionsPayload.items
          : [],
    );
    setHotels(Array.isArray(hotelsPayload.items) ? hotelsPayload.items : []);
  }

  useEffect(() => {
    startTransition(() => {
      loadAll().catch((loadError: unknown) => {
        setError(loadError instanceof Error ? loadError.message : "Failed to load admin access");
      });
    });
    // We intentionally load once on mount; refreshes are triggered explicitly after mutations.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.full_name.localeCompare(b.full_name)),
    [users],
  );
  const sortedRoles = useMemo(
    () => [...roles].sort((a, b) => a.code.localeCompare(b.code)),
    [roles],
  );
  const sortedHotels = useMemo(
    () => [...hotels].sort((a, b) => a.hotel_name.localeCompare(b.hotel_name)),
    [hotels],
  );

  async function saveUser() {
    setError("");
    setNotice("");
    const payload = {
      email: userForm.email.trim(),
      full_name: userForm.full_name.trim(),
      password: userForm.password.trim() || null,
      is_active: userForm.is_active,
      role_codes: userForm.role_codes,
      hotel_ids: userForm.hotel_ids,
    };
    const isEditing = Boolean(userForm.id);
    const response = await fetch(
      isEditing ? `${API_PREFIX}/api/admin/users/${userForm.id}` : `${API_PREFIX}/api/admin/users`,
      {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      throw new Error((await response.text()) || "Failed to save user");
    }
    await loadAll();
    setUserForm(EMPTY_USER_FORM);
    setNotice(isEditing ? "User updated." : "User created.");
  }

  async function deleteUser(user: AccessUser) {
    if (!window.confirm(`Delete user ${user.full_name}?`)) {
      return;
    }
    setError("");
    setNotice("");
    const response = await fetch(`${API_PREFIX}/api/admin/users/${user.id}`, { method: "DELETE" });
    if (!response.ok) {
      throw new Error((await response.text()) || "Failed to delete user");
    }
    await loadAll();
    if (userForm.id === user.id) {
      setUserForm(EMPTY_USER_FORM);
    }
    setNotice(`Deleted ${user.full_name}.`);
  }

  async function saveRole() {
    setError("");
    setNotice("");
    const payload = {
      code: roleForm.code.trim(),
      name: roleForm.name.trim(),
      description: roleForm.description.trim() || null,
      is_active: roleForm.is_active,
      permission_codes: roleForm.permission_codes,
    };
    const isEditing = Boolean(roleForm.id);
    const response = await fetch(
      isEditing ? `${API_PREFIX}/api/admin/roles/${roleForm.id}` : `${API_PREFIX}/api/admin/roles`,
      {
        method: isEditing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      throw new Error((await response.text()) || "Failed to save role");
    }
    await loadAll();
    setRoleForm(EMPTY_ROLE_FORM);
    setNotice(isEditing ? "Role updated." : "Role created.");
  }

  async function deleteRole(role: AccessRole) {
    if (!window.confirm(`Delete role ${role.code}?`)) {
      return;
    }
    setError("");
    setNotice("");
    const response = await fetch(`${API_PREFIX}/api/admin/roles/${role.id}`, { method: "DELETE" });
    if (!response.ok) {
      throw new Error((await response.text()) || "Failed to delete role");
    }
    await loadAll();
    if (roleForm.id === role.id) {
      setRoleForm(EMPTY_ROLE_FORM);
    }
    setNotice(`Deleted role ${role.code}.`);
  }

  function toggleSelection(values: string[], value: string) {
    return values.includes(value)
      ? values.filter((item) => item !== value)
      : [...values, value];
  }

  return (
    <WorkspaceShell
      mode="users"
      title="Users And Roles"
      subtitle="Manage admin, manager, member, sale and control feature access by role."
      statusLabel={`${users.length} users · ${roles.length} roles`}
    >
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-xl font-semibold text-slate-900">Current users</h3>
          <p className="mt-1 text-sm text-slate-500">
            Check each user, assigned role, and selected hotel scope from one table.
          </p>
          <div className="mt-5 space-y-3">
            {sortedUsers.map((user) => (
              <div key={user.id} className="rounded-[18px] border border-slate-200 bg-slate-50/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h4 className="text-lg font-semibold text-slate-900">{user.full_name}</h4>
                    <p className="mt-1 text-sm text-slate-500">
                      {user.email} · {user.is_active ? "active" : "inactive"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setUserForm(userFormFromUser(user))}
                      className="rounded-[10px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        startTransition(() => {
                          deleteUser(user).catch((actionError: unknown) => {
                            setError(actionError instanceof Error ? actionError.message : "Delete user failed");
                          });
                        });
                      }}
                      className="rounded-[10px] border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-[14px] border border-slate-200 bg-white p-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Roles</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {user.roles.map((role) => (
                        <span
                          key={role.id}
                          className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm text-slate-700"
                        >
                          {role.code}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-[14px] border border-slate-200 bg-white p-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Hotel scope</p>
                    <div className="mt-2 space-y-1 text-sm text-slate-600">
                      {user.hotel_ids.length ? user.hotel_ids.map((hotelId) => <p key={hotelId}>{hotelId}</p>) : <p>No hotel scope</p>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-semibold text-slate-900">{userForm.id ? "Edit user" : "Add user"}</h3>
              <p className="mt-1 text-sm text-slate-500">Assign role and hotel scope directly for each user.</p>
            </div>
            {userForm.id ? (
              <button
                type="button"
                onClick={() => setUserForm(EMPTY_USER_FORM)}
                className="rounded-[10px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
              >
                New
              </button>
            ) : null}
          </div>

          {error ? <div className="mt-4 rounded-[14px] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div> : null}
          {notice ? <div className="mt-4 rounded-[14px] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{notice}</div> : null}

          <div className="mt-5 grid gap-4">
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Full name
              <input
                value={userForm.full_name}
                onChange={(event) => setUserForm((current) => ({ ...current, full_name: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Email
              <input
                value={userForm.email}
                onChange={(event) => setUserForm((current) => ({ ...current, email: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Password {userForm.id ? "(leave blank to keep current password)" : ""}
              <input
                type="password"
                value={userForm.password}
                onChange={(event) => setUserForm((current) => ({ ...current, password: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="flex items-center gap-3 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={userForm.is_active}
                onChange={(event) => setUserForm((current) => ({ ...current, is_active: event.target.checked }))}
              />
              Active user
            </label>

            <div className="rounded-[16px] border border-slate-200 p-4">
              <p className="text-sm font-semibold text-slate-900">Roles</p>
              <div className="mt-3 grid gap-2">
                {sortedRoles.map((role) => (
                  <label key={role.id} className="flex items-start gap-3 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={userForm.role_codes.includes(role.code)}
                      onChange={() =>
                        setUserForm((current) => ({
                          ...current,
                          role_codes: toggleSelection(current.role_codes, role.code),
                        }))
                      }
                    />
                    <span>
                      <span className="font-semibold">{role.code}</span>
                      <span className="block text-slate-500">{role.description ?? "No description"}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="rounded-[16px] border border-slate-200 p-4">
              <p className="text-sm font-semibold text-slate-900">Hotel scope</p>
              <div className="mt-3 grid gap-2 max-h-56 overflow-auto">
                {sortedHotels.map((hotel) => (
                  <label key={hotel.id} className="flex items-center gap-3 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={userForm.hotel_ids.includes(hotel.id)}
                      onChange={() =>
                        setUserForm((current) => ({
                          ...current,
                          hotel_ids: toggleSelection(current.hotel_ids, hotel.id),
                        }))
                      }
                    />
                    <span>{hotel.hotel_name}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              type="button"
              disabled={isPending}
              onClick={() => {
                startTransition(() => {
                  saveUser().catch((actionError: unknown) => {
                    setError(actionError instanceof Error ? actionError.message : "Save user failed");
                  });
                });
              }}
              className="rounded-[14px] bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              {userForm.id ? "Update user" : "Create user"}
            </button>
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-xl font-semibold text-slate-900">Roles and permissions</h3>
          <p className="mt-1 text-sm text-slate-500">Role matrix to check what each user can access by feature.</p>
          <div className="mt-5 space-y-3">
            {sortedRoles.map((role) => (
              <div key={role.id} className="rounded-[18px] border border-slate-200 bg-slate-50/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h4 className="text-lg font-semibold text-slate-900">{role.name}</h4>
                    <p className="mt-1 text-sm text-slate-500">
                      {role.code} · {role.is_active ? "active" : "inactive"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setRoleForm(roleFormFromRole(role))}
                      className="rounded-[10px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        startTransition(() => {
                          deleteRole(role).catch((actionError: unknown) => {
                            setError(actionError instanceof Error ? actionError.message : "Delete role failed");
                          });
                        });
                      }}
                      className="rounded-[10px] border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {role.permissions.map((permission) => (
                    <span
                      key={permission.id}
                      className="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-700"
                    >
                      {permission.code}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-xl font-semibold text-slate-900">{roleForm.id ? "Edit role" : "Add role"}</h3>
              <p className="mt-1 text-sm text-slate-500">Set feature access by permission for each role.</p>
            </div>
            {roleForm.id ? (
              <button
                type="button"
                onClick={() => setRoleForm(EMPTY_ROLE_FORM)}
                className="rounded-[10px] border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
              >
                New
              </button>
            ) : null}
          </div>

          <div className="mt-5 grid gap-4">
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Role code
              <input
                value={roleForm.code}
                onChange={(event) => setRoleForm((current) => ({ ...current, code: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Role name
              <input
                value={roleForm.name}
                onChange={(event) => setRoleForm((current) => ({ ...current, name: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="grid gap-2 text-sm font-medium text-slate-700">
              Description
              <textarea
                rows={3}
                value={roleForm.description}
                onChange={(event) => setRoleForm((current) => ({ ...current, description: event.target.value }))}
                className="rounded-[12px] border border-slate-200 px-4 py-3 outline-none transition focus:border-slate-400"
              />
            </label>
            <label className="flex items-center gap-3 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={roleForm.is_active}
                onChange={(event) => setRoleForm((current) => ({ ...current, is_active: event.target.checked }))}
              />
              Active role
            </label>
            <div className="rounded-[16px] border border-slate-200 p-4">
              <p className="text-sm font-semibold text-slate-900">Permissions</p>
              <div className="mt-3 grid gap-2 max-h-72 overflow-auto">
                {permissions.map((permission) => (
                  <label key={permission.id} className="flex items-start gap-3 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={roleForm.permission_codes.includes(permission.code)}
                      onChange={() =>
                        setRoleForm((current) => ({
                          ...current,
                          permission_codes: toggleSelection(current.permission_codes, permission.code),
                        }))
                      }
                    />
                    <span>
                      <span className="font-semibold">{permission.code}</span>
                      <span className="block text-slate-500">{permission.description ?? permission.name}</span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <button
              type="button"
              disabled={isPending}
              onClick={() => {
                startTransition(() => {
                  saveRole().catch((actionError: unknown) => {
                    setError(actionError instanceof Error ? actionError.message : "Save role failed");
                  });
                });
              }}
              className="rounded-[14px] bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              {roleForm.id ? "Update role" : "Create role"}
            </button>
          </div>
        </div>
      </section>
    </WorkspaceShell>
  );
}
