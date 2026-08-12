import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import { knowledgeBaseApi, type KnowledgeBaseInfo } from '@/api';
import { authApi } from '@/api';
import {
  LayoutDashboard,
  Plus,
  LogOut,
  Settings,
  ChevronRight,
  BookOpen,
} from 'lucide-react';

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [kbList, setKbList] = useState<KnowledgeBaseInfo[]>([]);

  useEffect(() => {
    knowledgeBaseApi.list().then(setKbList).catch(() => {});
  }, [location.pathname]);

  const handleLogout = async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    logout();
    navigate('/login');
  };

  const currentKbId = location.pathname.match(/\/kb\/([^/]+)/)?.[1];

  return (
    <aside className="w-64 bg-[#0c1222] flex flex-col h-screen shrink-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <Link to="/dashboard" className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#0d9488] flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-sm">团队知识库</h1>
            <p className="text-slate-500 text-[10px]">Knowledge Base</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-3 py-4">
        {/* Dashboard */}
        <Link
          to="/dashboard"
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
            location.pathname === '/dashboard'
              ? 'bg-[#0d9488]/10 text-[#0d9488]'
              : 'text-slate-400 hover:text-white hover:bg-white/5'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>仪表盘</span>
        </Link>

        {/* Knowledge Bases */}
        <div className="mt-6">
          <div className="flex items-center justify-between px-3 mb-2">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
              知识库
            </span>
            <button
              onClick={() => navigate('/kb/create')}
              className="text-slate-500 hover:text-white transition-colors"
              title="创建知识库"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-0.5">
            {kbList.map((kb) => (
              <Link
                key={kb.knowledge_base_id}
                to={`/kb/${kb.knowledge_base_id}`}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all duration-200 group ${
                  currentKbId === kb.knowledge_base_id
                    ? 'bg-[#0d9488]/10 text-[#0d9488]'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <ChevronRight className={`w-3 h-3 transition-all duration-200 ${
                  currentKbId === kb.knowledge_base_id ? 'rotate-90' : ''
                } opacity-0 group-hover:opacity-100 ${
                  currentKbId === kb.knowledge_base_id ? 'opacity-100' : ''
                }`} />
                <span className="truncate">{kb.name}</span>
              </Link>
            ))}
            {kbList.length === 0 && (
              <p className="px-3 py-2 text-xs text-slate-600">暂无知识库</p>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="px-3 py-3 border-t border-white/10 space-y-1">
        <Link
          to="/profile"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-all duration-200"
        >
          <Settings className="w-4 h-4" />
          <span>个人设置</span>
        </Link>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/5 transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          <span>退出登录</span>
        </button>

        {user && (
          <div className="px-3 pt-2 border-t border-white/5 mt-1">
            <p className="text-xs text-slate-500 truncate">{user.display_name || user.username}</p>
          </div>
        )}
      </div>
    </aside>
  );
}
