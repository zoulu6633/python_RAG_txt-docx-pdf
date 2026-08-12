const API_BASE = 'http://localhost:8000';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    method: options.method || 'GET',
    headers,
  };

  if (options.body !== undefined) {
    if (options.body instanceof FormData) {
      config.body = options.body;
    } else {
      headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(options.body);
    }
  }

  const response = await fetch(`${API_BASE}${path}`, config);

  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('未登录');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(error.detail || `请求失败 (${response.status})`);
  }

  return response.json();
}

// ============ 用户认证 ============

export interface UserInfo {
  user_id: string;
  username: string;
  display_name: string | null;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: UserInfo;
}

export interface RegisterRequest {
  username: string;
  password: string;
  display_name?: string;
}

export const authApi = {
  login: (data: LoginRequest) =>
    request<TokenResponse>('/login', { method: 'POST', body: data }),

  register: (data: RegisterRequest) =>
    request<TokenResponse>('/register', { method: 'POST', body: data }),

  updateProfile: (data: { display_name: string }) =>
    request<UserInfo>('/update', { method: 'PUT', body: data }),

  changePassword: (data: { old_password: string; new_password: string }) =>
    request<{ message: string }>('/change-password', { method: 'PUT', body: data }),

  logout: () =>
    request<{ message: string }>('/logout', { method: 'POST' }),
};

// ============ 知识库 ============

export interface KnowledgeBaseInfo {
  knowledge_base_id: string;
  name: string;
  description: string | null;
  owner_id: string;
  visibility: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateKBRequest {
  name: string;
  description?: string;
  visibility?: string;
}

export interface UpdateKBRequest {
  name?: string;
  description?: string;
  visibility?: string;
}

export const knowledgeBaseApi = {
  list: () =>
    request<KnowledgeBaseInfo[]>('/knowledge/bases/list'),

  getById: (id: string) =>
    request<KnowledgeBaseInfo>(`/knowledge/bases/${id}`),

  create: (data: CreateKBRequest) =>
    request<KnowledgeBaseInfo>('/knowledge/bases/create', { method: 'POST', body: data }),

  update: (id: string, data: UpdateKBRequest) =>
    request<KnowledgeBaseInfo>(`/knowledge/bases/update/${id}`, { method: 'PUT', body: data }),

  delete: (id: string) =>
    request<{ message: string }>(`/knowledge/bases/delete/${id}`, { method: 'DELETE' }),
};

// ============ 文档 ============

export interface DocumentInfo {
  document_id: string;
  knowledge_base_id: string;
  title: string;
  original_file_name: string;
  content_type: string | null;
  file_ext: string | null;
  file_size: number | null;
  status: string;
  chunk_count: number | null;
  error_message: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export const documentApi = {
  listByKB: (kbId: string) =>
    request<DocumentInfo[]>(`/documents/knowledge-bases/${kbId}/documents`),

  upload: (kbId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<DocumentInfo>(`/documents/knowledge-bases/${kbId}/add`, {
      method: 'POST',
      body: formData,
    });
  },

  delete: (id: string) =>
    request<{ message: string; document_id: string; deleted_vector_count: number; deleted_physical_file: boolean }>(
      `/documents/remove/${id}`,
      { method: 'DELETE' }
    ),

  download: async (id: string, filename: string) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE}/documents/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '下载失败' }));
      throw new Error(error.detail || `下载失败 (${response.status})`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};

// ============ 成员 ============

export interface MemberInfo {
  knowledge_base_member_id: string;
  knowledge_base_id: string;
  user_id: string;
  username: string;
  display_name: string | null;
  role: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AddMemberRequest {
  username: string;
  role: string;
}

export const memberApi = {
  listByKB: (kbId: string) =>
    request<MemberInfo[]>(`/knowledge/bases/knowledge-bases/${kbId}/members`),

  add: (kbId: string, data: AddMemberRequest) =>
    request<MemberInfo>(`/knowledge/bases/knowledge-bases/${kbId}/members?member_name=${encodeURIComponent(data.username)}&role=${data.role}`, {
      method: 'POST',
    }),

  updateRole: (kbId: string, memberId: string, role: string) =>
    request<MemberInfo>(`/knowledge/bases/knowledge-bases/${kbId}/members/${memberId}`, {
      method: 'PUT',
      body: { role },
    }),

  remove: (kbId: string, memberId: string) =>
    request<{ message: string }>(`/knowledge/bases/knowledge-bases/${kbId}/members/${memberId}`, {
      method: 'DELETE',
    }),
};

// ============ 对话 ============

export interface ChatRequest {
  query: string;
  session_id?: string;
}

export interface SourceInfo {
  document_id: string;
  title: string;
  chunk_id: string;
  knowledge_base_name: string;
  score: number;
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceInfo[];
  session_id: string;
  source_count: number;
}

export interface SessionInfo {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageInfo {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Record<string, unknown> | null;
  created_at: string;
}

export const chatApi = {
  send: (kbId: string, data: ChatRequest) =>
    request<ChatResponse>(`/knowledge-bases/${kbId}/chat`, {
      method: 'POST',
      body: data,
    }),

  listSessions: (kbId: string) =>
    request<SessionInfo[]>(`/knowledge-bases/${kbId}/sessions`),

  getSessionMessages: (kbId: string, sessionId: string) =>
    request<ChatMessageInfo[]>(`/knowledge-bases/${kbId}/sessions/${sessionId}/messages`),

  deleteSession: (kbId: string, sessionId: string) =>
    request<{ success: boolean; message: string }>(`/knowledge-bases/${kbId}/sessions/${sessionId}`, {
      method: 'DELETE',
    }),

  renameSession: (kbId: string, sessionId: string, title: string) =>
    request<{ success: boolean; message: string }>(`/knowledge-bases/${kbId}/sessions/${sessionId}/title`, {
      method: 'PUT',
      body: { title },
    }),

  sendStream: (
    kbId: string,
    data: ChatRequest,
    callbacks: {
      onMetadata?: (meta: { session_id: string; sources: SourceInfo[]; source_count: number }) => void;
      onToken?: (token: string) => void;
      onDone?: () => void;
      onError?: (err: Error) => void;
    },
  ) => {
    const token = localStorage.getItem('token');
    const controller = new AbortController();

    fetch(`${API_BASE}/knowledge-bases/${kbId}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: '请求失败' }));
          throw new Error(error.detail || `请求失败 (${response.status})`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEvent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              const raw = line.slice(6);
              if (currentEvent === 'metadata' && callbacks.onMetadata) {
                callbacks.onMetadata(JSON.parse(raw));
              } else if (currentEvent === 'token' && callbacks.onToken) {
                callbacks.onToken(raw);
              } else if (currentEvent === 'done' && callbacks.onDone) {
                callbacks.onDone();
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name === 'AbortError') return;
        callbacks.onError?.(err);
      });

    return controller;
  },
};
