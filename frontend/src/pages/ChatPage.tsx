import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppLayout from '@/components/AppLayout';
import { chatApi, knowledgeBaseApi, type KnowledgeBaseInfo } from '@/api';
import ReactMarkdown from 'react-markdown';
import {
  ArrowLeft,
  Send,
  Loader2,
  MessageSquare,
  Sparkles,
  Bot,
  User,
  FileText,
  AlertCircle,
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: { document_id: string; title: string; chunk_id: string; knowledge_base_name: string; score: number; content: string }[];
}

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [kbInfo, setKbInfo] = useState<KnowledgeBaseInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!id) return;
    knowledgeBaseApi.getById(id).then(setKbInfo).catch(() => navigate(`/kb/${id}`));
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || loading || !id) return;

    const query = input.trim();
    const userMsg: Message = { id: `msg_${Date.now()}`, role: 'user', content: query };
    const assistantId = `msg_${Date.now() + 1}`;

    setMessages((prev) => [...prev, userMsg, { id: assistantId, role: 'assistant', content: '' }]);
    setInput('');
    setLoading(true);

    chatApi.sendStream(id, { query, session_id: sessionId }, {
      onMetadata: (meta) => {
        setSessionId(meta.session_id);
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
      onDone: () => setLoading(false),
      onError: (err) => {
        setMessages((prev) => {
          const copy = [...prev];
          const idx = copy.findIndex((m) => m.id === assistantId);
          if (idx !== -1) copy[idx] = { ...copy[idx], content: `对话功能暂未开放。\n\n> ${err.message}` };
          return copy;
        });
        setLoading(false);
      },
    });
  };

  return (
    <AppLayout>
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-8 py-4 shrink-0">
          <div className="max-w-4xl mx-auto flex items-center gap-4">
            <button
              onClick={() => navigate(`/kb/${id}`)}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[#0d9488]/10 flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-[#0d9488]" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-slate-800">{kbInfo?.name || '加载中...'}</h2>
                <p className="text-xs text-slate-400">知识库对话</p>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-4xl mx-auto px-8 py-8">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center pt-20 pb-12 animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-[#0d9488]/10 flex items-center justify-center mb-4">
                  <Sparkles className="w-8 h-8 text-[#0d9488]" />
                </div>
                <h3 className="text-xl font-semibold text-slate-800 mb-2">开始对话</h3>
                <p className="text-sm text-slate-500 text-center max-w-md">
                  你可以询问关于本知识库内文档的任何问题，AI 会基于文档内容为你解答
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className="mb-6 animate-slide-up">
                <div className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-[#0d9488] flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div className={`max-w-[75%] ${msg.role === 'user' ? 'order-1' : ''}`}>
                    {msg.role === 'user' ? (
                      <div className="bg-[#0d9488] text-white rounded-2xl rounded-tr-md px-4 py-2.5">
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
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
                      </div>
                    )}

                    {/* Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {msg.sources.map((source, idx) => (
                          <div key={idx} className="relative group">
                            <div className="flex items-center gap-1 px-2 py-1 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-500 cursor-default">
                              <FileText className="w-3 h-3" />
                              <span className="truncate max-w-[120px]">{source.title}</span>
                              <span className="text-slate-300">·</span>
                              <span className="text-[#0d9488] font-medium">
                                {(source.score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-2.5 bg-slate-800 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                              {source.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0 mt-0.5">
                      <User className="w-4 h-4 text-slate-500" />
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="mb-6 animate-slide-up">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#0d9488] flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 text-[#0d9488] animate-spin" />
                      <span className="text-sm text-slate-400">思考中...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {messages.length > 0 && (
              <div className="text-center mt-2 mb-4">
                <p className="text-xs text-slate-400">AI 回答仅供参考，请核实重要信息</p>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="bg-white border-t border-slate-200 px-8 py-4 shrink-0">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSend} className="flex items-center gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入你的问题..."
                disabled={loading}
                className="flex-1 px-4 py-2.5 border border-slate-300 rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-[#0d9488]/20 focus:border-[#0d9488]
                           transition-all duration-200 placeholder:text-slate-400 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="p-2.5 bg-[#0d9488] text-white rounded-xl hover:bg-[#0f766e]
                           transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
