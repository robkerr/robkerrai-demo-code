'use client'

import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const submitQuestion = async (question: string) => {
    if (!question.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: question.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Use Next.js API route as proxy
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userMessage.content }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer || 'Sorry, I could not generate a response.',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error fetching response:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await submitQuestion(input)
  }

  const handleSampleQuestionClick = (question: string) => {
    setInput(question)
    // Use setTimeout to ensure state is updated before submitting
    setTimeout(() => {
      submitQuestion(question)
    }, 0)
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>🎬 CineGraph</h1>
        <p>Ask me anything about movies, actors, directors, and genres!</p>
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Welcome to CineGraph! I'm your movie expert powered by GraphRAG.</p>
            <p className="examples">Try asking:</p>
            <div className="sample-questions">
              <button
                type="button"
                onClick={() => handleSampleQuestionClick('"Which Crime movies are Joe Pesci in?"')}
                disabled={isLoading}
                className="sample-question-button"
              >
                "Which Crime movies are Joe Pesci in?"
              </button>
              <button
                type="button"
                onClick={() => handleSampleQuestionClick('"Which films directed by Christopher Nolan was Christian Bale in?"')}
                disabled={isLoading}
                className="sample-question-button"
              >
                "Which films directed by Christopher Nolan was Christian Bale in?"
              </button>
              <button
                type="button"
                onClick={() => handleSampleQuestionClick('"What movies are about Frodo?"')}
                disabled={isLoading}
                className="sample-question-button"
              >
                "What movies are about Frodo?"
              </button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-content">
              {message.role === 'assistant' ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              ) : (
                message.content.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))
              )}
            </div>
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant-message">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about movies..."
          disabled={isLoading}
          className="chat-input"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="send-button"
        >
          {isLoading ? '...' : 'Send'}
        </button>
      </form>

      <style jsx>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100vh;
          max-width: 900px;
          margin: 0 auto;
          background: white;
          box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }

        .chat-header {
          padding: 2rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          text-align: center;
        }

        .chat-header h1 {
          font-size: 2.5rem;
          margin-bottom: 0.5rem;
        }

        .chat-header p {
          opacity: 0.9;
          font-size: 1rem;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 1.5rem;
          background: #f5f5f5;
        }

        .welcome-message {
          text-align: center;
          padding: 2rem;
          color: #666;
        }

        .welcome-message .examples {
          margin-top: 1rem;
          font-weight: bold;
        }

        .sample-questions {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          margin-top: 1rem;
          align-items: center;
        }

        .sample-question-button {
          width: 100%;
          max-width: 600px;
          padding: 0.75rem 1rem;
          background: white;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          font-style: italic;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s;
          text-align: left;
        }

        .sample-question-button:hover:not(:disabled) {
          border-color: #667eea;
          background: #f8f9ff;
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
        }

        .sample-question-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .message {
          margin-bottom: 1rem;
          display: flex;
          flex-direction: column;
        }

        .user-message {
          align-items: flex-end;
        }

        .assistant-message {
          align-items: flex-start;
        }

        .message-content {
          max-width: 70%;
          padding: 1rem 1.25rem;
          border-radius: 1rem;
          word-wrap: break-word;
        }

        .user-message .message-content {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .assistant-message .message-content {
          background: white;
          color: #333;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .message-content p {
          margin: 0.25rem 0;
        }

        /* Markdown styles for assistant messages */
        .assistant-message .message-content :global(h1),
        .assistant-message .message-content :global(h2),
        .assistant-message .message-content :global(h3),
        .assistant-message .message-content :global(h4),
        .assistant-message .message-content :global(h5),
        .assistant-message .message-content :global(h6) {
          margin: 0.75rem 0 0.5rem 0;
          font-weight: 600;
          line-height: 1.3;
        }

        .assistant-message .message-content :global(h1) {
          font-size: 1.5rem;
        }

        .assistant-message .message-content :global(h2) {
          font-size: 1.3rem;
        }

        .assistant-message .message-content :global(h3) {
          font-size: 1.1rem;
        }

        .assistant-message .message-content :global(ul),
        .assistant-message .message-content :global(ol) {
          margin: 0.5rem 0;
          padding-left: 1.5rem;
        }

        .assistant-message .message-content :global(li) {
          margin: 0.25rem 0;
        }

        .assistant-message .message-content :global(code) {
          background: #f4f4f4;
          padding: 0.2rem 0.4rem;
          border-radius: 3px;
          font-family: 'Courier New', monospace;
          font-size: 0.9em;
        }

        .assistant-message .message-content :global(pre) {
          background: #f4f4f4;
          padding: 0.75rem;
          border-radius: 6px;
          overflow-x: auto;
          margin: 0.5rem 0;
        }

        .assistant-message .message-content :global(pre code) {
          background: none;
          padding: 0;
        }

        .assistant-message .message-content :global(blockquote) {
          border-left: 3px solid #667eea;
          padding-left: 1rem;
          margin: 0.5rem 0;
          color: #666;
          font-style: italic;
        }

        .assistant-message .message-content :global(a) {
          color: #667eea;
          text-decoration: underline;
        }

        .assistant-message .message-content :global(strong) {
          font-weight: 600;
        }

        .assistant-message .message-content :global(em) {
          font-style: italic;
        }

        .assistant-message .message-content :global(hr) {
          border: none;
          border-top: 1px solid #e0e0e0;
          margin: 1rem 0;
        }

        .assistant-message .message-content :global(table) {
          border-collapse: collapse;
          width: 100%;
          margin: 1rem 0;
          font-size: 0.95em;
        }

        .assistant-message .message-content :global(th),
        .assistant-message .message-content :global(td) {
          border: 1px solid #e0e0e0;
          padding: 0.75rem;
          text-align: left;
        }

        .assistant-message .message-content :global(th) {
          background: #f4f4f4;
          font-weight: 600;
        }

        .assistant-message .message-content :global(tr:nth-child(even)) {
          background: #fafafa;
        }

        .assistant-message .message-content :global(p) {
          margin: 0.5rem 0;
        }

        .assistant-message .message-content :global(p:first-child) {
          margin-top: 0;
        }

        .assistant-message .message-content :global(p:last-child) {
          margin-bottom: 0;
        }

        .message-timestamp {
          font-size: 0.75rem;
          color: #999;
          margin-top: 0.25rem;
          padding: 0 0.5rem;
        }

        .typing-indicator {
          display: flex;
          gap: 0.5rem;
        }

        .typing-indicator span {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #667eea;
          animation: typing 1.4s infinite;
        }

        .typing-indicator span:nth-child(2) {
          animation-delay: 0.2s;
        }

        .typing-indicator span:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes typing {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
          }
          30% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }

        .input-form {
          display: flex;
          padding: 1rem;
          background: white;
          border-top: 1px solid #e0e0e0;
          gap: 0.5rem;
        }

        .chat-input {
          flex: 1;
          padding: 0.75rem 1rem;
          border: 2px solid #e0e0e0;
          border-radius: 1.5rem;
          font-size: 1rem;
          outline: none;
          transition: border-color 0.2s;
        }

        .chat-input:focus {
          border-color: #667eea;
        }

        .chat-input:disabled {
          background: #f5f5f5;
          cursor: not-allowed;
        }

        .send-button {
          padding: 0.75rem 2rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 1.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.2s;
        }

        .send-button:hover:not(:disabled) {
          opacity: 0.9;
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  )
}

