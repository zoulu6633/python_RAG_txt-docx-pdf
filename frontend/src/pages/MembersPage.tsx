import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppLayout from '@/components/AppLayout';
import { memberApi, type MemberInfo } from '@/api';
import { ArrowLeft, Users, UserPlus, Shield, Loader2, AlertCircle, Crown, UserCheck, User } from 'lucide-react';

const ROLE_LABELS: Record<string, string> = {
  owner: '拥有者',
  admin: '管理员',
  viewer: '查看者',
};

const ROLE_COLORS: Record<string, string> = {
  owner: 'text-amber-600 bg-amber-50 border-amber-200',
  admin: 'text-blue-600 bg-blue-50 border-blue-200',
  viewer: 'text-slate-600 bg-slate-50 border-slate-200',
};

const ROLE_ICONS: Record<string, typeof Crown> = {
  owner: Crown,
  admin: Shield,
  viewer: UserCheck,
};

export default function MembersPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [members, setMembers] = useState<MemberInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addUsername, setAddUsername] = useState('');
  const [addRole, setAddRole] = useState('viewer');
  const [addError, setAddError] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  useEffect(() => {
    if (!id) return;
    loadMembers();
  }, [id]);

  const loadMembers = async () => {
    if (!id) return;
    try {
      const data = await memberApi.listByKB(id);
      setMembers(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !addUsername.trim()) return;
    setAddLoading(true);
    setAddError('');
    try {
      await memberApi.add(id, { username: addUsername.trim(), role: addRole });
      setShowAddModal(false);
      setAddUsername('');
      setAddRole('viewer');
      loadMembers();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : '添加失败');
    } finally {
      setAddLoading(false);
    }
  };

  const currentUserId = localStorage.getItem('user_id');

  return (
    <AppLayout>
      <div className="max-w-4xl mx-auto px-8 py-8">
        <button
          onClick={() => navigate(`/kb/${id}`)}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          返回知识库
        </button>

        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">成员管理</h1>
            <p className="text-sm text-slate-500 mt-1">管理知识库的成员和角色权限</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#0d9488] text-white rounded-lg text-sm
                       font-medium hover:bg-[#0f766e] transition-all duration-200"
          >
            <UserPlus className="w-4 h-4" />
            添加成员
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden">
          {loading ? (
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
                const isSelf = member.user_id === currentUserId;
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
                            {isSelf && <span className="text-xs text-slate-400 ml-1">（你）</span>}
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

                    {!isOwner && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs text-slate-400 bg-slate-50 border border-slate-200/60">
                        <Shield className="w-3 h-3" />
                        角色管理暂未开放
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowAddModal(false)}>
          <div
            className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4 animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-900 mb-4">添加成员</h3>
            <form onSubmit={handleAddMember} className="space-y-4">
              {addError && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{addError}</span>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">用户名</label>
                <input
                  type="text"
                  value={addUsername}
                  onChange={(e) => setAddUsername(e.target.value)}
                  placeholder="输入要添加的用户名"
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                             focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                             transition-all duration-200"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">角色</label>
                <select
                  value={addRole}
                  onChange={(e) => setAddRole(e.target.value)}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                             focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]"
                >
                  <option value="admin">管理员 — 可管理成员和文档</option>
                  <option value="viewer">查看者 — 仅可查看和检索</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-all"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={addLoading || !addUsername.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-[#0d9488] text-white rounded-lg text-sm font-medium
                             hover:bg-[#0f766e] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {addLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                  {addLoading ? '添加中...' : '添加'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
