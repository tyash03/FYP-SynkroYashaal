'use client'

import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { chatApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Send, Sparkles, Loader2 } from 'lucide-react'
import type { ChatResponse } from '@/types'

interface Message {
  role: 'user' | 'assistant'
  content: string
  suggestedActions?: Array<{
    action: string
    label: string
    url: string
  }>
}

const SUGGESTED_QUERIES = [
  "What's on my plate this week?",
  "Show me overdue tasks",
  "Who's working on authentication?",
  "Summarize today's meetings",
  "What's the team's workload?",
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const chatMutation = useMutation({
    mutationFn: (message: string) => chatApi.query(message),
    onSuccess: (response: { data: ChatResponse }) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.response,
          suggestedActions: response.data.suggested_actions,
        },
      ])
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || chatMutation.isPending) return

    const userMessage = input.trim()
    setInput('')

    // Add user message
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])

    // Send to API
    chatMutation.mutate(userMessage)
  }

  const handleSuggestedQuery = (query: string) => {
    setInput(query)
  }

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">AI Assistant</h1>
        <p className="text-sm text-muted-foreground">
          Ask questions about your tasks, meetings, and team
        </p>
      </div>

      <div className="flex-1 flex gap-4 overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-white rounded-lg border overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Sparkles className="h-12 w-12 text-primary mb-4" />
                <h2 className="text-lg font-semibold mb-2">Ask me anything</h2>
                <p className="text-sm text-muted-foreground max-w-md">
                  I can help you find tasks, check team workload, summarize meetings, and more.
                </p>
              </div>
            ) : (
              <>
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-primary text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>

                      {message.suggestedActions && message.suggestedActions.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {message.suggestedActions.map((action, idx) => (
                            <a
                              key={idx}
                              href={action.url}
                              className="block px-3 py-2 text-xs font-medium bg-white text-gray-900 rounded border hover:bg-gray-50 transition-colors"
                            >
                              {action.label}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {chatMutation.isPending && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg px-4 py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="border-t p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={chatMutation.isPending}
              />
              <Button
                type="submit"
                disabled={!input.trim() || chatMutation.isPending}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </form>
        </div>

        {/* Suggested Queries Sidebar */}
        <Card className="w-64 p-4 hidden lg:block">
          <h3 className="font-semibold mb-3 text-sm">Suggested Queries</h3>
          <div className="space-y-2">
            {SUGGESTED_QUERIES.map((query, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuery(query)}
                className="w-full text-left text-sm px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {query}
              </button>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
