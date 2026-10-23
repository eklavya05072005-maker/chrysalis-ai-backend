'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Calendar,
  Plus,
  LogOut,
  Clock,
  CheckCircle,
  UploadCloud,
  FileText,
  AlertTriangle,
  History,
  Mail,
  ExternalLink,
  Edit,
  Trash2,
  Send,
  Eye,
} from 'lucide-react';
import { UrbenEvent, AdminUser, Enquiry, AuditLog, EventStatus } from '@/types';
import EventModal from '@/components/admin/EventModal';

interface AdminDashboardProps {
  initialUser: AdminUser;
  onLogout: () => void;
}

export default function AdminDashboard({ initialUser, onLogout }: AdminDashboardProps) {
  const [user] = useState<AdminUser>(initialUser);
  const [activeTab, setActiveTab] = useState<'events' | 'enquiries' | 'audit'>('events');
  const [events, setEvents] = useState<UrbenEvent[]>([]);
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<{ text: string; isError?: boolean } | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<UrbenEvent | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const [eventsRes, enquiriesRes, auditRes] = await Promise.all([
        fetch('/api/admin/events'),
        fetch('/api/enquiries'),
        fetch('/api/admin/audit'),
      ]);

      if (eventsRes.ok) {
        const data = await eventsRes.json();
        setEvents(data.events || []);
      }
      if (enquiriesRes.ok) {
        const data = await enquiriesRes.json();
        setEnquiries(data.enquiries || []);
      }
      if (auditRes.ok) {
        const data = await auditRes.json();
        setAuditLogs(data.logs || []);
      }
    } catch {
      setActionMessage({ text: 'Error fetching latest data', isError: true });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleStatusTransition = async (eventId: string, newStatus: EventStatus) => {
    setActionMessage(null);
    try {
      const res = await fetch(`/api/admin/events/${eventId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });

      const data = await res.json();
      if (!res.ok) {
        setActionMessage({ text: data.error || 'Status update denied', isError: true });
      } else {
        setActionMessage({ text: `Event transitioned to ${newStatus.toUpperCase()}` });
        fetchDashboardData();
      }
    } catch {
      setActionMessage({ text: 'Network failure during status update', isError: true });
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (!confirm('Are you sure you want to permanently delete this event?')) return;
    try {
      const res = await fetch(`/api/admin/events/${eventId}`, { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok) {
        setActionMessage({ text: data.error || 'Delete failed', isError: true });
      } else {
        setActionMessage({ text: 'Event deleted successfully' });
        fetchDashboardData();
      }
    } catch {
      setActionMessage({ text: 'Network error deleting event', isError: true });
    }
  };

  const getStatusBadge = (status: EventStatus) => {
    switch (status) {
      case 'draft':
        return (
          <span className="px-2.5 py-1 text-[10px] font-mono uppercase bg-zinc-800 text-zinc-300 border border-zinc-700">
            DRAFT
          </span>
        );
      case 'review_pending':
        return (
          <span className="px-2.5 py-1 text-[10px] font-mono uppercase bg-yellow-950/80 text-yellow-400 border border-yellow-700/60 animate-pulse">
            REVIEW PENDING
          </span>
        );
      case 'approved':
        return (
          <span className="px-2.5 py-1 text-[10px] font-mono uppercase bg-blue-950/80 text-blue-400 border border-blue-700/60">
            APPROVED
          </span>
        );
      case 'published':
        return (
          <span className="px-2.5 py-1 text-[10px] font-mono uppercase bg-emerald-950/80 text-emerald-400 border border-emerald-700/60">
            PUBLISHED (LIVE)
          </span>
        );
      case 'archived':
        return (
          <span className="px-2.5 py-1 text-[10px] font-mono uppercase bg-zinc-900 text-zinc-500 border border-zinc-800">
            ARCHIVED
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#080808] text-brand-silver">
      {/* Admin Top Navigation */}
      <header className="bg-[#111111] border-b border-white/10 px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <Link
            href="/"
            className="text-lg font-display font-black tracking-widest text-white uppercase"
          >
            URBEN<span className="text-brand-red">.</span>ENTT
          </Link>
          <span className="hidden sm:inline-block px-2.5 py-0.5 text-[10px] font-mono uppercase bg-white/5 border border-white/10 text-zinc-400">
            CONTROL CENTER
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-xs font-mono text-white font-bold">{user.fullName}</div>
            <div className="text-[10px] font-mono uppercase text-brand-red font-semibold">
              ROLE: {user.role.replace('_', ' ')}
            </div>
          </div>

          <Link
            href="/"
            target="_blank"
            className="p-2 text-zinc-400 hover:text-white"
            title="View Public Site"
          >
            <Eye className="w-4 h-4" />
          </Link>

          <button
            type="button"
            onClick={onLogout}
            className="p-2 text-zinc-400 hover:text-brand-red transition-colors"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Banner Alert if any */}
        {actionMessage && (
          <div
            className={`mb-6 p-4 text-xs font-mono border flex items-center justify-between ${
              actionMessage.isError
                ? 'bg-red-950/70 border-brand-red text-white'
                : 'bg-emerald-950/70 border-emerald-600 text-white'
            }`}
          >
            <span>{actionMessage.text}</span>
            <button
              type="button"
              onClick={() => setActionMessage(null)}
              className="text-zinc-400 hover:text-white text-sm"
            >
              ✕
            </button>
          </div>
        )}

        {/* Tab Header & Action Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4 mb-8">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setActiveTab('events')}
              className={`px-4 py-2 text-xs font-mono uppercase tracking-wider flex items-center space-x-2 transition-colors ${
                activeTab === 'events'
                  ? 'bg-brand-red text-white font-bold'
                  : 'bg-white/5 text-zinc-400 hover:text-white'
              }`}
            >
              <Calendar className="w-3.5 h-3.5" />
              <span>Events & Workflow ({events.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('enquiries')}
              className={`px-4 py-2 text-xs font-mono uppercase tracking-wider flex items-center space-x-2 transition-colors ${
                activeTab === 'enquiries'
                  ? 'bg-brand-red text-white font-bold'
                  : 'bg-white/5 text-zinc-400 hover:text-white'
              }`}
            >
              <Mail className="w-3.5 h-3.5" />
              <span>Enquiries ({enquiries.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('audit')}
              className={`px-4 py-2 text-xs font-mono uppercase tracking-wider flex items-center space-x-2 transition-colors ${
                activeTab === 'audit'
                  ? 'bg-brand-red text-white font-bold'
                  : 'bg-white/5 text-zinc-400 hover:text-white'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Audit History</span>
            </button>
          </div>

          {activeTab === 'events' && (
            <button
              type="button"
              onClick={() => {
                setEditingEvent(null);
                setIsModalOpen(true);
              }}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-white/10 hover:bg-brand-red text-white text-xs font-mono uppercase tracking-wider font-bold transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>Create Event Draft</span>
            </button>
          )}
        </div>

        {/* TAB 1: EVENTS */}
        {activeTab === 'events' && (
          <div className="space-y-4">
            {events.length === 0 ? (
              <div className="p-12 text-center bg-[#111111] border border-white/10">
                <p className="text-sm font-mono text-zinc-400">No events found.</p>
              </div>
            ) : (
              <div className="overflow-x-auto border border-white/10 bg-[#111111]">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#181818] border-b border-white/10 text-zinc-400 uppercase">
                    <tr>
                      <th className="p-4">Event & Category</th>
                      <th className="p-4">Date / Venue</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Created By</th>
                      <th className="p-4 text-right">Workflow Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {events.map((evt) => (
                      <tr key={evt.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="p-4">
                          <div className="font-bold text-white text-sm uppercase flex items-center space-x-2">
                            <span>{evt.title}</span>
                            {evt.isFeatured && (
                              <span className="px-1.5 py-0.5 text-[9px] bg-brand-red text-white uppercase">
                                FEATURED
                              </span>
                            )}
                          </div>
                          <div className="text-[11px] text-zinc-500 mt-0.5">{evt.category}</div>
                          <div className="text-[10px] text-zinc-600">/{evt.slug}</div>
                        </td>

                        <td className="p-4 text-zinc-300">
                          <div>{evt.timeDisplay}</div>
                          <div className="text-zinc-500">{evt.venueName}, {evt.city}</div>
                        </td>

                        <td className="p-4">{getStatusBadge(evt.status)}</td>

                        <td className="p-4 text-zinc-400">
                          <div>{evt.createdBy}</div>
                          {evt.approvedBy && (
                            <div className="text-[10px] text-zinc-600">
                              Apprv: {evt.approvedBy}
                            </div>
                          )}
                        </td>

                        <td className="p-4 text-right space-x-2">
                          {/* Event Admin Actions */}
                          {user.role === 'event_admin' && (
                            <>
                              {evt.status === 'draft' && (
                                <button
                                  type="button"
                                  onClick={() => handleStatusTransition(evt.id, 'review_pending')}
                                  className="px-2.5 py-1 bg-yellow-950/80 hover:bg-yellow-800 text-yellow-300 border border-yellow-700/60 uppercase text-[10px]"
                                  title="Submit to Owner for Review"
                                >
                                  Submit Review
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => {
                                  setEditingEvent(evt);
                                  setIsModalOpen(true);
                                }}
                                className="p-1.5 text-zinc-400 hover:text-white"
                                title="Edit Draft"
                              >
                                <Edit className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}

                          {/* Owner / Developer Full Publishing Powers */}
                          {user.role !== 'event_admin' && (
                            <>
                              {evt.status === 'review_pending' && (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => handleStatusTransition(evt.id, 'approved')}
                                    className="px-2 py-1 bg-blue-900 hover:bg-blue-800 text-blue-200 uppercase text-[10px]"
                                  >
                                    Approve
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleStatusTransition(evt.id, 'published')}
                                    className="px-2 py-1 bg-emerald-900 hover:bg-emerald-800 text-emerald-200 uppercase text-[10px]"
                                  >
                                    Approve & Publish
                                  </button>
                                </>
                              )}

                              {evt.status === 'approved' && (
                                <button
                                  type="button"
                                  onClick={() => handleStatusTransition(evt.id, 'published')}
                                  className="px-2 py-1 bg-emerald-900 hover:bg-emerald-800 text-emerald-200 uppercase text-[10px]"
                                >
                                  Publish Live
                                </button>
                              )}

                              {evt.status === 'published' && (
                                <button
                                  type="button"
                                  onClick={() => handleStatusTransition(evt.id, 'draft')}
                                  className="px-2 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 uppercase text-[10px]"
                                >
                                  Unpublish to Draft
                                </button>
                              )}

                              {evt.status === 'draft' && (
                                <button
                                  type="button"
                                  onClick={() => handleStatusTransition(evt.id, 'published')}
                                  className="px-2 py-1 bg-emerald-950/80 hover:bg-emerald-800 text-emerald-300 border border-emerald-700/60 uppercase text-[10px]"
                                >
                                  Quick Publish
                                </button>
                              )}

                              <button
                                type="button"
                                onClick={() => {
                                  setEditingEvent(evt);
                                  setIsModalOpen(true);
                                }}
                                className="p-1.5 text-zinc-400 hover:text-white"
                                title="Edit Event"
                              >
                                <Edit className="w-3.5 h-3.5" />
                              </button>

                              <button
                                type="button"
                                onClick={() => handleDeleteEvent(evt.id)}
                                className="p-1.5 text-zinc-500 hover:text-brand-red"
                                title="Delete Event"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: ENQUIRIES */}
        {activeTab === 'enquiries' && (
          <div className="space-y-4">
            {enquiries.length === 0 ? (
              <div className="p-12 text-center bg-[#111111] border border-white/10">
                <p className="text-sm font-mono text-zinc-400">No client enquiries received yet.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {enquiries.map((enq) => (
                  <div key={enq.id} className="p-6 bg-[#111111] border border-white/10 space-y-3 font-mono text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-brand-red font-bold uppercase">{enq.enquiryType}</span>
                      <span className="text-zinc-500">{new Date(enq.createdAt).toLocaleDateString()}</span>
                    </div>

                    <h4 className="text-base font-display font-bold text-white uppercase">
                      {enq.fullName}
                    </h4>

                    <div className="text-zinc-400 space-y-1">
                      <div>Email: <a href={`mailto:${enq.email}`} className="text-white hover:underline">{enq.email}</a></div>
                      {enq.phone && <div>Phone: <span className="text-white">{enq.phone}</span></div>}
                      {enq.eventDate && <div>Target Date: <span className="text-white">{enq.eventDate}</span></div>}
                      {enq.estimatedGuests && <div>Est. Guests: <span className="text-white">{enq.estimatedGuests}</span></div>}
                    </div>

                    <div className="p-3 bg-black/40 border border-white/5 text-zinc-300 leading-relaxed font-sans text-xs">
                      {enq.message}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: AUDIT TRAIL */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <div className="overflow-x-auto border border-white/10 bg-[#111111]">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#181818] border-b border-white/10 text-zinc-400 uppercase">
                  <tr>
                    <th className="p-4">Timestamp</th>
                    <th className="p-4">Action</th>
                    <th className="p-4">Entity</th>
                    <th className="p-4">Actor</th>
                    <th className="p-4">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-white/[0.02]">
                      <td className="p-4 text-zinc-400">
                        {new Date(log.createdAt).toLocaleString()}
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 bg-brand-red/10 border border-brand-red/30 text-brand-red font-bold">
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 text-zinc-300">{log.entityType} ({log.entityId})</td>
                      <td className="p-4 text-zinc-400">{log.userEmail}</td>
                      <td className="p-4 text-zinc-500 max-w-xs truncate">
                        {log.details ? JSON.stringify(log.details) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Event Edit / Create Modal */}
      {isModalOpen && (
        <EventModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSaved={() => {
            fetchDashboardData();
            setActionMessage({ text: 'Event saved successfully' });
          }}
          event={editingEvent}
          user={user}
        />
      )}
    </div>
  );
}
