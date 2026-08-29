import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import AppLayout from '@/components/AppLayout';
import {
  knowledgeBaseApi, documentApi, memberApi, chatApi,
  type KnowledgeBaseInfo, type DocumentInfo, type MemberInfo, type SourceInfo,
  type SessionInfo, type ChatMessageInfo,
} from '@/api';
import { relevanceScoreStyle } from '@/lib/utils';
import {
  ArrowLeft, FileText, Users, MessageSquare, Trash2, Upload, Loader2, Download,
  Clock, CheckCircle2, XCircle, AlertCircle, RefreshCcw, Lock, Globe,
  UserPlus, User, Crown, UserCheck, UserX, Shield, Send, Bot, Plus,
  MoreVertical, Pencil,
} from 'lucide-react';

type TabType = 'documents' | 'members' | 'chat';
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceInfo[];
}

export default function KBDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [kb, setKb] = useState<KnowledgeBaseInfo | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('documents');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  // Members state
  const [members, setMembers] = useState<MemberInfo[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [addUsername, setAddUsername] = useState('');
  const [addMemberRole, setAddMemberRole] = useState('viewer');
  const [addMemberError, setAddMemberError] = useState('');
  const [addMemberLoading, setAddMemberLoading] = useState(false);
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null);
  const [memberError, setMemberError] = useState('');

  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();
  const [menuOpenSessionId, setMenuOpenSessionId] = useState<string | null>(null);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renameTitle, setRenameTitle] = useState('');
  const [renameSessionId, setRenameSessionId] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!id) return;
    loadKB();
    loadDocuments();
    // 切换知识库时重置对话状态
    setMessages([]);
    setSessionId(undefined);
    setActiveSessionId(undefined);
    setInput('');
    setMenuOpenSessionId(null);
    setShowRenameModal(false);
  }, [id]);

  const loadKB = async () => {
    if (!id) return;
    try {
      const data = await knowledgeBaseApi.getById(id);
      setKb(data);
    } catch {
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    if (!id) return;
    try {
      const docs = await documentApi.listByKB(id);
      setDocuments(docs);
    } catch {
      // ignore
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    setDeletingDoc(docId);
    try {
      await documentApi.delete(docId);
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
    } catch (err) {
      alert(err instanceof Error ? err.message : '删除失败');
    } finally {
      setDeletingDoc(null);
    }
  };

  const handleDeleteKB = async () => {
    if (!id) return;
    try {
      await knowledgeBaseApi.delete(id);
      navigate('/dashboard');
    } catch (err) {
      alert(err instanceof Error ? err.message : '删除失败');
    }
  };

  const handleUpload = async () => {
    if (!id || !uploadFile) return;
    setUploadLoading(true);
    setUploadError('');
    try {
      await documentApi.upload(id, uploadFile);
      setShowUploadModal(false);
      setUploadFile(null);
      loadDocuments();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setUploadLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!['.txt', '.pdf', '.docx'].includes(ext)) {
        setUploadError('仅支持 .txt、.pdf、.docx 格式');
        return;
      }
      setUploadFile(file);
      setUploadError('');
    }
  };

  // ── Members ──
  const loadMembers = useCallback(async () => {
    if (!id) return;
    setMembersLoading(true);
    try {
      const data = await memberApi.listByKB(id);
      setMembers(data);
    } catch {
      // ignore
    } finally {
      setMembersLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (activeTab === 'members' && id) loadMembers();
  }, [activeTab, id, loadMembers]);

  const currentUserId = localStorage.getItem('user_id');
  const currentUserMember = members.find((m) => m.user_id === currentUserId);
  const canManageMembers = currentUserMember && ['owner', 'admin'].includes(currentUserMember.role);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !addUsername.trim()) return;
    setAddMemberLoading(true);
    setAddMemberError('');
    try {
      await memberApi.add(id, { username: addUsername.trim(), role: addMemberRole });
      setShowAddMemberModal(false);
      setAddUsername('');
      setAddMemberRole('viewer');
      loadMembers();
    } catch (err) {
      setAddMemberError(err instanceof Error ? err.message : '添加失败');
    } finally {
      setAddMemberLoading(false);
    }
  };

  const handleRoleChange = async (memberId: string, newRole: string) => {
    if (!id) return;
    setUpdatingMemberId(memberId);
    setMemberError('');
    try {
      await memberApi.updateRole(id, memberId, newRole);
      loadMembers();
    } catch (err) {
      setMemberError(err instanceof Error ? err.message : '修改失败');
    } finally {
      setUpdatingMemberId(null);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!id || !window.confirm('确定要移除该成员吗？')) return;
    setUpdatingMemberId(memberId);
    setMemberError('');
    try {
      await memberApi.remove(id, memberId);
      loadMembers();
    } catch (err) {
      setMemberError(err instanceof Error ? err.message : '移除失败');
    } finally {
      setUpdatingMemberId(null);
    }
  };

  // ── Chat ──
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (activeTab === 'chat' && id) loadSessions();
  }, [activeTab, id]);

  const loadSessions = useCallback(async () => {
    if (!id) return;
    setSessionsLoading(true);
    try {
      const data = await chatApi.listSessions(id);
      setSessions(data);
    } catch {
      // ignore
    } finally {
      setSessionsLoading(false);
    }
  }, [id]);

  const handleSwitchSession = async (sid: string) => {
    if (!id) return;
    setActiveSessionId(sid);
    setSessionId(sid);
    setMessages([]);
    setChatLoading(true);
    try {
      const data = await chatApi.getSessionMessages(id, sid);
      setMessages(data.map((m: ChatMessageInfo) => ({
        id: m.message_id,
        role: m.role,
        content: m.content,
      })));
    } catch {
      // ignore
    } finally {
      setChatLoading(false);
    }
  };

  const handleNewSession = () => {
    setActiveSessionId(undefined);
    setSessionId(undefined);
    setMessages([]);
  };

  // 点击其他地方关闭菜单
  useEffect(() => {
    const handler = () => setMenuOpenSessionId(null);
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, []);

  const handleDeleteSession = async (sid: string) => {
    if (!id || !window.confirm('确定要删除该会话吗？')) return;
    setMenuOpenSessionId(null);
    try {
      await chatApi.deleteSession(id, sid);
      if (activeSessionId === sid) {
        setActiveSessionId(undefined);
        setSessionId(undefined);
        setMessages([]);
      }
      loadSessions();
    } catch (err) {
      alert(err instanceof Error ? err.message : '删除失败');
    }
  };

  const openRenameModal = (sid: string, currentTitle: string) => {
    setRenameSessionId(sid);
    setRenameTitle(currentTitle);
    setShowRenameModal(true);
    setMenuOpenSessionId(null);
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !renameSessionId || !renameTitle.trim()) return;
    try {
      await chatApi.renameSession(id, renameSessionId, renameTitle.trim());
      setShowRenameModal(false);
      loadSessions();
    } catch (err) {
      alert(err instanceof Error ? err.message : '重命名失败');
    }
  };

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || chatLoading || !id) return;

    const query = input.trim();
    const userMsg: Message = { id: `msg_${Date.now()}`, role: 'user', content: query };
    const assistantId = `msg_${Date.now() + 1}`;

    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: 'assistant', content: '' }]);
    setInput('');
    setChatLoading(true);

    chatApi.sendStream(id, { query, session_id: sessionId }, {
      onMetadata: (meta) => {
        setSessionId(meta.session_id);
        setActiveSessionId(meta.session_id);
        setMessages((prev) => {
          const copy = [...prev];
          const idx = copy.findIndex((m) => m.id === assistantId);
          if (idx !== -1) copy[idx] = { ...copy[idx], sources: meta.sources };
          return copy;
        });
      },
      onToken: (token) => {
        setMessages((prev) => {
          const copy = [...prev];
          const idx = copy.findIndex((m) => m.id === assistantId);
          if (idx !== -1) copy[idx] = { ...copy[idx], content: copy[idx].content + token };
          return copy;
        });
      },
      onDone: () => {
        setChatLoading(false);
        loadSessions();
      },
      onError: (err) => {
        setMessages((prev) => {
          const copy = [...prev];
          const idx = copy.findIndex((m) => m.id === assistantId);
          if (idx !== -1) copy[idx] = { ...copy[idx], content: `请求失败：${err.message}` };
          return copy;
        });
        setChatLoading(false);
      },
    });
  };

  const ROLE_LABELS: Record<string, string> = {
    owner: '拥有者', admin: '管理员', viewer: '查看者',
  };
  const ROLE_COLORS: Record<string, string> = {
    owner: 'text-amber-600 bg-amber-50 border-amber-200',
    admin: 'text-blue-600 bg-blue-50 border-blue-200',
    viewer: 'text-slate-600 bg-slate-50 border-slate-200',
  };
  const ROLE_ICONS: Record<string, typeof Crown> = { owner: Crown, admin: Shield, viewer: UserCheck };

  const formatSize = (bytes: number | null) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'ready':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'uploaded':
        return <RefreshCcw className="w-4 h-4 text-amber-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const statusText = (status: string) => {
    switch (status) {
      case 'ready':
        return '就绪';
      case 'failed':
        return '失败';
      case 'uploaded':
        return '处理中';
      default:
        return status;
    }
  };

  const tabs: { key: TabType; label: string; icon: typeof FileText }[] = [
    { key: 'documents', label: '文档', icon: FileText },
    { key: 'members', label: '成员', icon: Users },
    { key: 'chat', label: '对话', icon: MessageSquare },
  ];

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <Loader2 className="w-6 h-6 text-[#0d9488] animate-spin" />
        </div>
      </AppLayout>
    );
  }

  if (!kb) return null;

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            返回知识库列表
          </button>

          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#0d9488]/10 flex items-center justify-center">
                <FileText className="w-6 h-6 text-[#0d9488]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-slate-900">
                    {kb.name}
                  </h1>
                  {kb.visibility === 'private' ? (
                    <Lock className="w-4 h-4 text-slate-400" />
                  ) : (
                    <Globe className="w-4 h-4 text-slate-400" />
                  )}
                </div>
                <p className="text-sm text-slate-500 mt-0.5">{kb.description || '暂无描述'}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-[#0d9488] text-white rounded-lg text-sm
                           font-medium hover:bg-[#0f766e] transition-all duration-200"
              >
                <Upload className="w-4 h-4" />
                上传文档
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-slate-200">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all duration-200 ${
                  activeTab === tab.key
                    ? 'border-[#0d9488] text-[#0d9488]'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden animate-fade-in">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">文件名</th>
                    <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">类型</th>
                    <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">大小</th>
                    <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">状态</th>
                    <th className="text-left px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">上传时间</th>
                    <th className="text-right px-5 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {documents.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-5 py-12 text-center">
                        <div className="flex flex-col items-center gap-2">
                          <FileText className="w-8 h-8 text-slate-300" />
                          <p className="text-sm text-slate-500">该知识库暂无文档</p>
                        </div>
                      </td>
                    </tr>
                  )}
                  {documents.map((doc) => (
                    <tr key={doc.document_id} className="hover:bg-slate-50/50 transition-colors group">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center">
                            <FileText className="w-4 h-4 text-slate-500" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-800">{doc.title}</p>
                            <p className="text-xs text-slate-400">{doc.original_file_name}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-xs text-slate-500 uppercase">{(doc.file_ext || '').replace('.', '') || '-'}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-sm text-slate-600">{formatSize(doc.file_size)}</span>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1.5">
                          {statusIcon(doc.status)}
                          <span className="text-sm text-slate-600">{statusText(doc.status)}</span>
                          {doc.error_message && (
                            <span className="relative group">
                              <AlertCircle className="w-3.5 h-3.5 text-red-400 ml-1" />
                              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded
                                           opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                {doc.error_message}
                              </span>
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-sm text-slate-500">{formatDate(doc.created_at)}</span>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => documentApi.download(doc.document_id, doc.original_file_name || doc.title)}
                            className="p-1.5 text-slate-400 hover:text-blue-500 hover:bg-blue-50 rounded transition-all"
                            title="下载"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteDoc(doc.document_id)}
                            disabled={deletingDoc === doc.document_id}
                            className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-all"
                            title="删除"
                          >
                            {deletingDoc === doc.document_id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Members Tab */}
        {activeTab === 'members' && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-slate-500">管理知识库的成员和权限</p>
              {canManageMembers && (
                <button
                  onClick={() => setShowAddMemberModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-[#0d9488] text-white rounded-lg text-sm
                             font-medium hover:bg-[#0f766e] transition-all"
                >
                  <UserPlus className="w-4 h-4" />
                  添加成员
                </button>
              )}
            </div>

            <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden">
              {memberError && (
                <div className="flex items-center gap-2 px-5 py-3 bg-red-50 border-b border-red-200 text-red-600 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{memberError}</span>
                </div>
              )}
              {membersLoading ? (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="w-6 h-6 text-[#0d9488] animate-spin" />
                </div>
              ) : members.length === 0 ? (
                <div className="py-16 text-center">
                  <Users className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-sm text-slate-500">暂无成员</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {members.map((member) => {
                    const RoleIcon = ROLE_ICONS[member.role] || User;
                    const isOwner = member.role === 'owner';
                    return (
                      <div key={member.knowledge_base_member_id} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50/50 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                            <User className="w-5 h-5 text-slate-500" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-slate-800">
                                {member.display_name || member.username}
                                {member.user_id === currentUserId && <span className="text-xs text-slate-400 ml-1">（你）</span>}
                              </p>
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${
                                ROLE_COLORS[member.role] || ROLE_COLORS.viewer
                              }`}>
                                <RoleIcon className="w-3 h-3" />
                                {ROLE_LABELS[member.role] || member.role}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">
                              加入于 {new Date(member.created_at).toLocaleDateString('zh-CN')}
                            </p>
                          </div>
                        </div>

                        {!isOwner && canManageMembers && (
                          <div className="flex items-center gap-2">
                            <select
                              value={member.role}
                              onChange={(e) => handleRoleChange(member.knowledge_base_member_id, e.target.value)}
                              disabled={updatingMemberId === member.knowledge_base_member_id}
                              className="px-2 py-1 text-xs border border-slate-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488] disabled:opacity-50"
                            >
                              <option value="admin">管理员</option>
                              <option value="viewer">查看者</option>
                            </select>
                            <button
                              onClick={() => handleRemoveMember(member.knowledge_base_member_id)}
                              disabled={updatingMemberId === member.knowledge_base_member_id}
                              className="flex items-center gap-1 px-2 py-1 text-xs text-red-500 hover:bg-red-50 border border-transparent hover:border-red-200 rounded-md transition-all disabled:opacity-50"
                            >
                              {updatingMemberId === member.knowledge_base_member_id ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <UserX className="w-3 h-3" />
                              )}
                              移除
                            </button>
                          </div>
                        )}
                        {!isOwner && !canManageMembers && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs text-slate-400 bg-slate-50 border border-slate-200/60">
                            <Shield className="w-3 h-3" />
                            暂无管理权限
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <div className="animate-fade-in flex gap-4 h-[calc(100vh-280px)]">
            {/* Session Sidebar */}
            <div className="w-56 shrink-0 bg-white rounded-xl border border-slate-200/60 shadow-sm flex flex-col overflow-hidden">
              <div className="p-3 border-b border-slate-100">
                <button
                  onClick={handleNewSession}
                  className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    !activeSessionId
                      ? 'bg-[#0d9488] text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <Plus className="w-4 h-4" />
                  新对话
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                {sessionsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-5 h-5 text-[#0d9488] animate-spin" />
                  </div>
                ) : sessions.length === 0 ? (
                  <div className="py-8 text-center">
                    <p className="text-xs text-slate-400">暂无历史会话</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-50">
                    {sessions.map((s) => (
                      <div key={s.session_id} className="relative group">
                        <button
                          onClick={() => handleSwitchSession(s.session_id)}
                          className={`w-full text-left px-3 py-2.5 pr-8 transition-colors hover:bg-slate-50 ${
                            activeSessionId === s.session_id ? 'bg-[#0d9488]/5 border-l-2 border-[#0d9488]' : ''
                          }`}
                        >
                          <p className="text-sm text-slate-700 truncate">{s.title}</p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {new Date(s.updated_at).toLocaleDateString('zh-CN')}
                          </p>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setMenuOpenSessionId(menuOpenSessionId === s.session_id ? null : s.session_id);
                          }}
                          className="absolute right-1 top-1/2 -translate-y-1/2 p-1 rounded text-slate-300 hover:text-slate-600 hover:bg-slate-100 opacity-0 group-hover:opacity-100 transition-all"
                        >
                          <MoreVertical className="w-3.5 h-3.5" />
                        </button>
                        {menuOpenSessionId === s.session_id && (
                          <div
                            className="absolute right-1 top-8 z-20 bg-white border border-slate-200 rounded-lg shadow-lg py-1 w-28"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              onClick={() => openRenameModal(s.session_id, s.title)}
                              className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                              重命名
                            </button>
                            <button
                              onClick={() => handleDeleteSession(s.session_id)}
                              className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-red-500 hover:bg-red-50"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              删除
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col min-w-0">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
                {messages.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center py-16">
                    <Bot className="w-12 h-12 text-slate-300 mb-3" />
                    <p className="text-sm font-medium text-slate-600">开始和知识库对话</p>
                    <p className="text-xs text-slate-400 mt-1">输入问题，AI 将基于已上传的文档回答</p>
                  </div>
                )}
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                    {msg.role === 'assistant' && (
                      <div className="w-8 h-8 rounded-full bg-[#0d9488]/10 flex items-center justify-center shrink-0">
                        <Bot className="w-4 h-4 text-[#0d9488]" />
                      </div>
                    )}
                    <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                      {msg.role === 'user' ? (
                        <div className="bg-[#0d9488] text-white rounded-2xl rounded-tr-md px-4 py-2.5 text-sm shadow-sm">
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      ) : (
                        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
                          {msg.content ? (
                            <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-slate-800 prose-code:text-sm">
                              <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1 text-sm text-slate-400">
                              <span className="w-1.5 h-4 bg-[#0d9488] animate-pulse" />
                              <span>思考中...</span>
                            </div>
                          )}
                          {msg.sources && msg.sources.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1.5 border-t border-slate-100 pt-2">
                              {msg.sources.map((src, idx) => (
                                <div key={idx} className="relative group">
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-500 cursor-default">
                                    <FileText className="w-3 h-3" />
                                    <span className="truncate max-w-[100px]">{src.title}</span>
                                    <span className="text-slate-300">·</span>
                                    <span
                                      className={`font-medium ${relevanceScoreStyle(src.score)}`}
                                      title={`重排相关性 ${(src.score * 100).toFixed(0)}%`}
                                    >
                                      {(src.score * 100).toFixed(0)}%
                                    </span>
                                  </span>
                                  {src.content && (
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-2.5 bg-slate-800 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                                      {src.content}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={handleSend} className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="输入你的问题..."
                  disabled={chatLoading}
                  className="flex-1 px-4 py-3 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488] transition-all disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || chatLoading}
                  className="flex items-center gap-2 px-5 py-3 bg-[#0d9488] text-white rounded-xl text-sm font-medium hover:bg-[#0f766e] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {chatLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {chatLoading ? '' : '发送'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* Rename Session Modal */}
      {showRenameModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowRenameModal(false)}>
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-900 mb-5">重命名会话</h3>
            <form onSubmit={handleRenameSubmit}>
              <input
                type="text"
                value={renameTitle}
                onChange={(e) => setRenameTitle(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488] mb-5"
                autoFocus
              />
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowRenameModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={!renameTitle.trim()}
                  className="px-4 py-2 bg-[#0d9488] text-white rounded-lg text-sm font-medium hover:bg-[#0f766e] transition-all disabled:opacity-50"
                >
                  保存
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => { setShowUploadModal(false); setUploadError(''); setUploadFile(null); }}>
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-900 mb-1">上传文档</h3>
            <p className="text-sm text-slate-500 mb-5">支持 .txt、.pdf、.docx 格式</p>

            {uploadError && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm mb-4">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}

            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
                ${uploadFile ? 'border-[#0d9488] bg-[#0d9488]/5' : 'border-slate-300 hover:border-slate-400'}`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.pdf,.docx"
                className="hidden"
                onChange={handleFileSelect}
              />
              {uploadFile ? (
                <div>
                  <FileText className="w-8 h-8 text-[#0d9488] mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-800">{uploadFile.name}</p>
                  <p className="text-xs text-slate-400 mt-1">{(uploadFile.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div>
                  <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">点击选择文件</p>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-3 mt-5">
              <button
                onClick={() => { setShowUploadModal(false); setUploadError(''); setUploadFile(null); }}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-all"
              >
                取消
              </button>
              <button
                onClick={handleUpload}
                disabled={!uploadFile || uploadLoading}
                className="flex items-center gap-2 px-4 py-2 bg-[#0d9488] text-white rounded-lg text-sm font-medium
                           hover:bg-[#0f766e] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploadLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                {uploadLoading ? '上传中...' : '上传'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Member Modal */}
      {showAddMemberModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => { setShowAddMemberModal(false); setAddMemberError(''); }}>
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-md w-full mx-4 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-900 mb-1">添加成员</h3>
            <p className="text-sm text-slate-500 mb-5">输入用户名并选择角色</p>

            {addMemberError && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm mb-4">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{addMemberError}</span>
              </div>
            )}

            <form onSubmit={handleAddMember}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">用户名</label>
                <input
                  type="text"
                  value={addUsername}
                  onChange={(e) => setAddUsername(e.target.value)}
                  placeholder="输入用户名"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]"
                  required
                />
              </div>
              <div className="mb-5">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">角色</label>
                <select
                  value={addMemberRole}
                  onChange={(e) => setAddMemberRole(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]"
                >
                  <option value="viewer">查看者</option>
                  <option value="admin">管理员</option>
                </select>
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => { setShowAddMemberModal(false); setAddMemberError(''); }}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={!addUsername.trim() || addMemberLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-[#0d9488] text-white rounded-lg text-sm font-medium hover:bg-[#0f766e] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {addMemberLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                  {addMemberLoading ? '添加中...' : '添加'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete KB Confirm Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowDeleteConfirm(false)}>
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-900 mb-2">删除知识库</h3>
            <p className="text-sm text-slate-600 mb-6">
              确定要删除"<strong>{kb.name}</strong>"吗？该操作不可撤销，所有文档和向量数据将被删除。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-all"
              >
                取消
              </button>
              <button
                onClick={handleDeleteKB}
                className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 transition-all"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
