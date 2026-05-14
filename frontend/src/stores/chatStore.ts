import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatState, ChatSession, Message } from '../types/chat';
import { generateId } from '../lib/utils';

interface ChatActions {
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string) => void;
  createSession: () => string;
  deleteSession: (sessionId: string) => void;
  setCurrentSession: (sessionId: string) => void;
  setLoading: (loading: boolean) => void;
  clearCurrentSession: () => void;
}

type ChatStore = ChatState & ChatActions;

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      sessions: [],
      currentSessionId: null,
      isLoading: false,

      addMessage: (message) => set((state) => {
        const { currentSessionId } = state;
        if (!currentSessionId) return state;

        const newMessage: Message = {
          ...message,
          id: generateId(),
          timestamp: Date.now(),
        };

        return {
          sessions: state.sessions.map((session) =>
            session.id === currentSessionId
              ? {
                  ...session,
                  messages: [...session.messages, newMessage],
                  // 如果是第一条用户消息，更新标题
                  title: session.messages.length === 0 && message.role === 'user'
                    ? message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
                    : session.title,
                }
              : session
          ),
        };
      }),

      updateLastMessage: (content) => set((state) => {
        const { currentSessionId } = state;
        if (!currentSessionId) return state;

        return {
          sessions: state.sessions.map((session) =>
            session.id === currentSessionId && session.messages.length > 0
              ? {
                  ...session,
                  messages: session.messages.map((msg, idx) =>
                    idx === session.messages.length - 1
                      ? { ...msg, content }
                      : msg
                  ),
                }
              : session
          ),
        };
      }),

      createSession: () => {
        const id = generateId();
        const newSession: ChatSession = {
          id,
          title: 'New Chat',
          messages: [],
          createdAt: Date.now(),
        };
        set((state) => ({
          sessions: [newSession, ...state.sessions],
          currentSessionId: id,
        }));
        return id;
      },

      deleteSession: (sessionId) => set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        currentSessionId: state.currentSessionId === sessionId
          ? null
          : state.currentSessionId,
      })),

      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),

      setLoading: (loading) => set({ isLoading: loading }),

      clearCurrentSession: () => set((state) => {
        const { currentSessionId } = state;
        if (!currentSessionId) return state;

        return {
          sessions: state.sessions.map((session) =>
            session.id === currentSessionId
              ? { ...session, messages: [] }
              : session
          ),
        };
      }),
    }),
    {
      name: 'chat-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
      }),
    }
  )
);
