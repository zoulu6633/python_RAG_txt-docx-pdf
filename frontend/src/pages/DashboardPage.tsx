import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '@/components/AppLayout';
import { knowledgeBaseApi, type KnowledgeBaseInfo } from '@/api';
import { Plus, BookOpen, Users, FileText, Clock, Loader2, Globe, Lock } from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [kbList, setKbList] = useState<KnowledgeBaseInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, owner: 0, member: 0 });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const list = await knowledgeBaseApi.list();
      setKbList(list);
      setStats({
        total: list.length,
        owner: list.filter((kb) => kb.owner_id === localStorage.getItem('user_id')).length,
        member: list.length,
      });
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  };

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">我的知识库</h1>
            <p className="text-slate-500 mt-1 text-sm">管理和浏览你的所有知识库</p>
          </div>
          <button
            onClick={() => navigate('/kb/create')}
            className="flex items-center gap-2 px-4 py-2.5 bg-[#0d9488] text-white rounded-lg text-sm
                       font-medium hover:bg-[#0f766e] transition-all duration-200 shadow-sm shadow-[#0d9488]/20"
          >
            <Plus className="w-4 h-4" />
            创建知识库
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl p-5 border border-slate-200/60 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#0d9488]/10 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-[#0d9488]" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                <p className="text-xs text-slate-500">知识库总数</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-5 border border-slate-200/60 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <Users className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.member}</p>
                <p className="text-xs text-slate-500">参与的知识库</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-5 border border-slate-200/60 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                <FileText className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">-</p>
                <p className="text-xs text-slate-500">文档总数</p>
              </div>
            </div>
          </div>
        </div>

        {/* KB List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-6 h-6 text-[#0d9488] animate-spin" />
          </div>
        ) : kbList.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-16 text-center">
            <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">还没有知识库</h3>
            <p className="text-sm text-slate-500 mb-6">创建一个知识库，开始管理团队知识文档</p>
            <button
              onClick={() => navigate('/kb/create')}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#0d9488] text-white
                         rounded-lg text-sm font-medium hover:bg-[#0f766e] transition-all duration-200"
            >
              <Plus className="w-4 h-4" />
              创建知识库
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {kbList.map((kb) => (
              <div
                key={kb.knowledge_base_id}
                onClick={() => navigate(`/kb/${kb.knowledge_base_id}`)}
                className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5
                           hover:shadow-md hover:border-slate-300 transition-all duration-200 cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg bg-[#0d9488]/10 flex items-center justify-center group-hover:bg-[#0d9488]/20 transition-colors">
                    <BookOpen className="w-5 h-5 text-[#0d9488]" />
                  </div>
                  {kb.visibility === 'private' ? (
                    <Lock className="w-3.5 h-3.5 text-slate-400" />
                  ) : (
                    <Globe className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </div>
                <h3 className="font-semibold text-slate-900 mb-1 truncate">{kb.name}</h3>
                <p className="text-xs text-slate-500 mb-4 line-clamp-2 min-h-[2rem]">
                  {kb.description || '暂无描述'}
                </p>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDate(kb.updated_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
