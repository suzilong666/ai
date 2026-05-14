import { useState, useCallback, useRef } from 'react';
import { useChatStore } from '../stores/chatStore';
import type { Message } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useChat() {
  const { addMessage, updateLastMessage, setLoading, currentSessionId } = useChatStore();
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !currentSessionId) return;

    // 添加用户消息
    const userMessage: Omit<Message, 'id' | 'timestamp'> = {
      role: 'user',
      content: content.trim(),
    };
    addMessage(userMessage);

    // 创建空的助手消息用于流式更新
    addMessage({
      role: 'assistant',
      content: '',
    });

    setLoading(true);
    setError(null);

    abortControllerRef.current = new AbortController();

    try {
      // 获取当前会话的所有消息
      const store = useChatStore.getState();
      const session = store.sessions.find((s) => s.id === currentSessionId);
      // 过滤掉空内容的消息，避免后端验证失败
      const messages = session?.messages
        .filter((m) => m.content.trim().length > 0)
        .map((m) => ({
          role: m.role,
          content: m.content,
        })) || [];

      const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages,
          stream: true,
          temperature: 0.7,
          model_name: 'glm-4',
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is not readable');
      }

      const decoder = new TextDecoder();
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        accumulatedText += chunk;
        updateLastMessage(accumulatedText);
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Request aborted');
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }, [currentSessionId, addMessage, updateLastMessage, setLoading]);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setLoading(false);
  }, [setLoading]);

  return {
    sendMessage,
    stopGeneration,
    error,
  };
}
