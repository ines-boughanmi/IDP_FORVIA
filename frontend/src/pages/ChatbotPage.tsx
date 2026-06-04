import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { SectionCard } from '@/components/ui/SectionCard';
import { LoadingState } from '@/components/ui/LoadingState';
import { fetchChatbotQuery } from '@/services/backendApi';

type Message = { role: 'user' | 'assistant'; text: string };

export function ChatbotPage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const messagesRef = useRef<HTMLDivElement | null>(null);

  const mutation = useMutation({
    mutationFn: (question: string) => fetchChatbotQuery(question),
    onSuccess(data) {
      console.log('chat response', data);
      const ans = (data && (data as any).answer) || (data && (data as any).data && (data as any).data.answer) || 'No response received from chatbot';
      setMessages((m) => [...m, { role: 'assistant', text: ans }]);
    },
    onError(err) {
      console.error('chat error', err);
      setMessages((m) => [...m, { role: 'assistant', text: 'Chatbot request failed. Please try again.' }]);
    },
  });

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages, mutation.isLoading]);

  function send() {
    if (!input.trim()) return;
    const question = input.trim();
    setMessages((m) => [...m, { role: 'user', text: question }]);
    setInput('');
    mutation.mutate(question);
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Conversational analysis</p>
          <h1>Chatbot</h1>
          <p>Posez des questions en langage naturel sur les fournisseurs, transactions et anomalies.</p>
        </div>
      </div>

      <SectionCard title="AI Risk Assistant" description="Ask questions about suppliers, transactions and risks.">
        <div className="chat-area">
          <div className="messages" ref={messagesRef} style={{ maxHeight: 420, overflowY: 'auto' }}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-message ${m.role}`}>
                <div className="message-bubble">{m.text}</div>
              </div>
            ))}
            {mutation.isLoading && (
              <div className="chat-message assistant">
                <div className="message-bubble">Thinking...</div>
              </div>
            )}
          </div>

          <div className="chat-input-row">
            <input
              placeholder="Ask a question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
            />
            <button onClick={send} disabled={mutation.isLoading}>
              {mutation.isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>

          {mutation.isError && <div className="callout error">Error: {(mutation.error as any)?.message || 'Request failed'}</div>}
        </div>
      </SectionCard>
    </div>
  );
}

export default ChatbotPage;
