import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '@/components/AppLayout';
import { knowledgeBaseApi } from '@/api';
import { ArrowLeft, Save, Loader2, AlertCircle } from 'lucide-react';

export default function CreateKBPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [visibility, setVisibility] = useState('private');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('请输入知识库名称');
      return;
    }

    setLoading(true);
    try {
      const kb = await knowledgeBaseApi.create({
        name: name.trim(),
        description: description.trim() || undefined,
        visibility,
      });
      navigate(`/kb/${kb.knowledge_base_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto px-8 py-8">
        {/* Back */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          返回
        </button>

        <h1 className="text-2xl font-bold text-slate-900 mb-1">创建知识库</h1>
        <p className="text-sm text-slate-500 mb-8">创建一个新的知识空间来管理团队文档</p>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-8 space-y-6">
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              知识库名称 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例如：算法团队知识库"
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                         transition-all duration-200 placeholder:text-slate-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              描述
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="简要描述这个知识库的用途（选填）"
              rows={3}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm resize-none
                         focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                         transition-all duration-200 placeholder:text-slate-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">
              可见性
            </label>
            <div className="flex gap-3">
              <label
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 border rounded-lg cursor-pointer
                           text-sm font-medium transition-all duration-200 ${
                  visibility === 'private'
                    ? 'border-[#0d9488] bg-[#0d9488]/5 text-[#0d9488]'
                    : 'border-slate-300 text-slate-600 hover:border-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="visibility"
                  value="private"
                  checked={visibility === 'private'}
                  onChange={() => setVisibility('private')}
                  className="sr-only"
                />
                私密
              </label>
              <label
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 border rounded-lg cursor-pointer
                           text-sm font-medium transition-all duration-200 ${
                  visibility === 'public'
                    ? 'border-[#0d9488] bg-[#0d9488]/5 text-[#0d9488]'
                    : 'border-slate-300 text-slate-600 hover:border-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="visibility"
                  value="public"
                  checked={visibility === 'public'}
                  onChange={() => setVisibility('public')}
                  className="sr-only"
                />
                公开
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2.5 border border-slate-300 rounded-lg text-sm text-slate-600
                         hover:bg-slate-50 transition-all duration-200"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 bg-[#0d9488] text-white rounded-lg text-sm
                         font-medium hover:bg-[#0f766e] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {loading ? '创建中...' : '创建知识库'}
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  );
}
