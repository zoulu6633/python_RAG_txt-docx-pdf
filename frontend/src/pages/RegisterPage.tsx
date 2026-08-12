import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthLayout from '@/components/AuthLayout';
import { authApi } from '@/api';
import { useAuthStore } from '@/store/auth';
import { UserPlus, Loader2, AlertCircle } from 'lucide-react';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username.trim()) {
      setError('请输入用户名');
      return;
    }
    if (!password.trim()) {
      setError('请输入密码');
      return;
    }
    if (password.length < 6) {
      setError('密码长度不能少于6位');
      return;
    }
    if (password !== confirmPassword) {
      setError('两次密码输入不一致');
      return;
    }

    setLoading(true);
    try {
      const res = await authApi.register({
        username: username.trim(),
        password,
        display_name: displayName.trim() || undefined,
      });
      setAuth(res.access_token, res.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="创建账号" subtitle="加入团队知识库，开始协作">
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            用户名 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="用于登录的用户名"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                       focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                       transition-all duration-200 placeholder:text-slate-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            昵称
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="显示名称（选填）"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                       focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                       transition-all duration-200 placeholder:text-slate-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            密码 <span className="text-red-500">*</span>
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="至少6位密码"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                       focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                       transition-all duration-200 placeholder:text-slate-400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            确认密码 <span className="text-red-500">*</span>
          </label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="再次输入密码"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                       focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                       transition-all duration-200 placeholder:text-slate-400"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[#0d9488] text-white
                     rounded-lg text-sm font-medium hover:bg-[#0f766e] transition-all duration-200
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <UserPlus className="w-4 h-4" />
          )}
          {loading ? '注册中...' : '注 册'}
        </button>

        <p className="text-center text-sm text-slate-500">
          已有账号？{' '}
          <Link to="/login" className="text-[#0d9488] hover:text-[#0f766e] font-medium transition-colors">
            立即登录
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
