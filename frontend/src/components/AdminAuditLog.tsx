// frontend/src/components/AdminAuditLog.tsx

import React, { useState, useEffect } from 'react';

interface AuditLogEntry {
  id: number;
  timestamp: string;
  username: string;
  action: string;
  details: string;
  ip_address: string;
}

export function AdminAuditLog() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/admin/audit-logs', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
      .then(res => res.json())
      .then(data => {
        setLogs(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-slate-400 bg-slate-950 min-h-screen">Loading audit logs...</div>;
  }

  return (
    <div className="p-8 bg-slate-950 text-slate-100 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">System Audit Trail</h1>
          <p className="text-sm text-slate-400 mt-1">Immutable security and access event logs for compliance verification.</p>
        </div>
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-800/60 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">User</th>
              <th className="py-3 px-4">Action</th>
              <th className="py-3 px-4">Details</th>
              <th className="py-3 px-4">IP Address</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-sm font-mono text-slate-300">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-slate-500">No audit records found.</td>
              </tr>
            ) : (
              logs.map(log => (
                <tr key={log.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 px-4 text-xs text-slate-400">{log.timestamp}</td>
                  <td className="py-3 px-4 text-blue-400 font-medium">{log.username}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 text-xs rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {log.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-xs text-slate-300">{log.details}</td>
                  <td className="py-3 px-4 text-xs text-slate-500">{log.ip_address}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}