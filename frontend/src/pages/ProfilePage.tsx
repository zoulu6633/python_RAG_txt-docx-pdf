import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '@/components/AppLayout';
import { authApi } from '@/api';
import { useAuthStore } from '@/store/auth';
import { ArrowLeft, Save, Loader2, AlertCircle, User, Calendar, Lock, Eye, EyeOff } from 'lucide-react';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, updateUser, logout } = useAuthStore();
  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // Password change state
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!displayName.trim()) {
      setError('昵称不能为空');
      return;
    }

    setSaving(true);
    try {
      const user = await authApi.updateProfile({ display_name: displayName.trim() });
      updateUser(user);
      setSuccess('个人资料已更新');
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新失败');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (!oldPassword) { setPasswordError('请输入原密码'); return; }
    if (!newPassword) { setPasswordError('请输入新密码'); return; }
    if (newPassword.length < 6) { setPasswordError('新密码长度不能少于6位'); return; }
    if (newPassword !== confirmPassword) { setPasswordError('两次输入的新密码不一致'); return; }

    setChangingPassword(true);
    try {
      const result = await authApi.changePassword({ old_password: oldPassword, new_password: newPassword });
      setPasswordSuccess(result.message);
      // 修改成功后自动登出并跳转到登录页
      setTimeout(() => {
        logout();
        navigate('/login', { replace: true });
      }, 1500);
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : '修改失败');
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto px-8 py-8">
        <a
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          返回首页
        </a>

        <h1 className="text-2xl font-bold text-slate-900 mb-1">个人设置</h1>
        <p className="text-sm text-slate-500 mb-8">管理你的个人资料信息</p>

        <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden">
          {/* User Info Header */}
          <div className="px-8 py-6 border-b border-slate-100">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-[#0d9488]/10 flex items-center justify-center">
                <User className="w-7 h-7 text-[#0d9488]" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{user?.display_name || user?.username}</h2>
                <p className="text-sm text-slate-500">@{user?.username}</p>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-8 py-6 space-y-6">
            {success && (
              <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                <Calendar className="w-4 h-4 shrink-0" />
                <span>{success}</span>
              </div>
            )}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">用户名</label>
              <input
                type="text"
                value={user?.username || ''}
                disabled
                className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm bg-slate-50 text-slate-400 cursor-not-allowed"
              />
              <p className="text-xs text-slate-400 mt-1">用户名不可修改</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">昵称</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="输入你的昵称"
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                           transition-all duration-200 placeholder:text-slate-400"
              />
            </div>

            {user?.created_at && (
              <div className="text-xs text-slate-400">
                注册时间：{new Date(user.created_at).toLocaleDateString('zh-CN')}
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 px-5 py-2.5 bg-[#0d9488] text-white rounded-lg text-sm
                           font-medium hover:bg-[#0f766e] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {saving ? '保存中...' : '保存修改'}
              </button>
            </div>
          </form>
        </div>

        {/* Password Change */}
        <div className="mt-8 bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden">
          <div className="px-8 py-4 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-slate-500" />
              <h3 className="text-base font-semibold text-slate-900">修改密码</h3>
            </div>
            <button
              onClick={() => { setShowPasswordForm(!showPasswordForm); setPasswordError(''); setPasswordSuccess(''); }}
              className="text-sm text-[#0d9488] hover:text-[#0f766e] font-medium transition-colors"
            >
              {showPasswordForm ? '收起' : '修改'}
            </button>
          </div>

          {showPasswordForm && (
            <form onSubmit={handleChangePassword} className="px-8 py-6 space-y-5">
              {passwordSuccess && (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                  <Calendar className="w-4 h-4 shrink-0" />
                  <span>{passwordSuccess}</span>
                </div>
              )}
              {passwordError && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{passwordError}</span>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">原密码</label>
                <div className="relative">
                  <input
                    type={showOld ? 'text' : 'password'}
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    placeholder="输入原密码"
                    className="w-full px-4 py-2.5 pr-10 border border-slate-300 rounded-lg text-sm
                               focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                               transition-all duration-200 placeholder:text-slate-400"
                  />
                  <button type="button" onClick={() => setShowOld(!showOld)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                    {showOld ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">新密码</label>
                <div className="relative">
                  <input
                    type={showNew ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="输入新密码（至少6位）"
                    className="w-full px-4 py-2.5 pr-10 border border-slate-300 rounded-lg text-sm
                               focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                               transition-all duration-200 placeholder:text-slate-400"
                  />
                  <button type="button" onClick={() => setShowNew(!showNew)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                    {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">确认新密码</label>
                <div className="relative">
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="再次输入新密码"
                    className="w-full px-4 py-2.5 pr-10 border border-slate-300 rounded-lg text-sm
                               focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                               transition-all duration-200 placeholder:text-slate-400"
                  />
                  <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                    {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={changingPassword}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#0d9488] text-white rounded-lg text-sm
                             font-medium hover:bg-[#0f766e] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {changingPassword ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  {changingPassword ? '修改中...' : '确认修改'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
