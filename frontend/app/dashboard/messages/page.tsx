'use client'

import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dmApi } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { MessageSquare, Send, Loader2, User, Plus, RefreshCw } from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'

interface TeamMember {
  id: string
  full_name: string
  email: string
  role: string
  avatar_url: string | null
}

interface Conversation {
  user_id: string
  full_name: string
  email: string
  avatar_url: string | null
  last_message: string
  last_timestamp: string
  is_sent: boolean
}

interface Message {
  id: string
  sender_id: string
  content: string
  created_at: string
  is_sent: boolean
}

function Avatar({ name, url, size = 9 }: { name: string; url?: string | null; size?: number }) {
  const cls = `h-${size} w-${size} rounded-full flex items-center justify-center text-xs font-bold shrink-0`
  if (url) return <img src={url} alt={name} className={`${cls} object-cover`} />
  return (
    <div className={`${cls} bg-primary text-primary-foreground`}>
      {name.slice(0, 2).toUpperCase()}
    </div>
  )
}

export default function MessagesPage() {
  const queryClient = useQueryClient()
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)
  const [showNewDm, setShowNewDm] = useState(false)
  const [text, setText] = useState('')
  const [syncMsg, setSyncMsg] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: conversations = [], isLoading: convsLoading } = useQuery({
    queryKey: ['dm-conversations'],
    queryFn: async () => (await dmApi.getConversations()).data as Conversation[],
    refetchInterval: 5000,
  })

  const { data: members = [], isLoading: membersLoading } = useQuery({
    queryKey: ['dm-users'],
    queryFn: async () => (await dmApi.getUsers()).data as TeamMember[],
    enabled: showNewDm,
  })

  const { data: activeConv, isLoading: msgsLoading } = useQuery({
    queryKey: ['dm-messages', selectedUserId],
    queryFn: async () => (await dmApi.getConversation(selectedUserId!)).data,
    enabled: !!selectedUserId,
    refetchInterval: 3000,
  })

  const sendMutation = useMutation({
    mutationFn: ({ recipientId, content }: { recipientId: string; content: string }) =>
      dmApi.sendMessage(recipientId, content),
    onSuccess: () => {
      setText('')
      queryClient.invalidateQueries({ queryKey: ['dm-messages', selectedUserId] })
      queryClient.invalidateQueries({ queryKey: ['dm-conversations'] })
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConv?.messages])

  const handleSend = () => {
    if (!text.trim() || !selectedUserId) return
    sendMutation.mutate({ recipientId: selectedUserId, content: text.trim() })
  }

  const syncMutation = useMutation({
    mutationFn: () => dmApi.syncFromSlack(),
    onSuccess: (res: { data: { synced: number; message: string } }) => {
      setSyncMsg(res.data.message)
      queryClient.invalidateQueries({ queryKey: ['dm-conversations'] })
      if (selectedUserId) queryClient.invalidateQueries({ queryKey: ['dm-messages', selectedUserId] })
      setTimeout(() => setSyncMsg(null), 4000)
    },
    onError: (err: any) => {
      setSyncMsg(err?.response?.data?.detail || 'Sync failed')
      setTimeout(() => setSyncMsg(null), 4000)
    },
  })

  const handleSelectUser = (userId: string) => {
    setSelectedUserId(userId)
    setShowNewDm(false)
  }

  const selectedUser = activeConv?.user ?? conversations.find(c => c.user_id === selectedUserId)

  return (
    <div className="space-y-4 h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Direct Messages</h1>
          <p className="text-sm text-muted-foreground">Message your team members</p>
        </div>
        <div className="flex items-center gap-2">
          {syncMsg && (
            <span className="text-xs text-muted-foreground">{syncMsg}</span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            title="Sync DMs from Slack"
          >
            {syncMutation.isPending
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <RefreshCw className="h-4 w-4" />}
            <span className="ml-1 hidden sm:inline">Sync Slack</span>
          </Button>
          <Button onClick={() => { setShowNewDm(true); setSelectedUserId(null) }} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            New Message
          </Button>
        </div>
      </div>

      <div className="flex gap-4" style={{ height: 'calc(100vh - 14rem)' }}>
        {/* Sidebar */}
        <div className="w-72 shrink-0 flex flex-col gap-2 overflow-y-auto">
          {convsLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-primary" /></div>
          ) : conversations.length === 0 ? (
            <Card className="p-6 text-center">
              <MessageSquare className="h-8 w-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-muted-foreground">No conversations yet</p>
              <p className="text-xs text-muted-foreground mt-1">Click "New Message" to start one.</p>
            </Card>
          ) : (
            <Card className="overflow-hidden">
              <CardContent className="p-0 divide-y">
                {conversations.map((conv) => (
                  <button
                    key={conv.user_id}
                    onClick={() => handleSelectUser(conv.user_id)}
                    className={`w-full text-left px-3 py-3 hover:bg-muted/50 transition-colors flex items-start gap-3 ${
                      selectedUserId === conv.user_id ? 'bg-primary/10' : ''
                    }`}
                  >
                    <Avatar name={conv.full_name} url={conv.avatar_url} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">{conv.full_name}</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {conv.is_sent ? 'You: ' : ''}{conv.last_message}
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap shrink-0 mt-0.5">
                      {formatRelativeTime(conv.last_timestamp)}
                    </span>
                  </button>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Main panel */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* New DM – pick a user */}
          {showNewDm && (
            <Card className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b">
                <h2 className="font-semibold">Select a team member</h2>
              </div>
              <div className="p-4 flex-1 overflow-y-auto">
                {membersLoading ? (
                  <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-primary" /></div>
                ) : members.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">No other team members found.</p>
                ) : (
                  <div className="space-y-1">
                    {members.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => handleSelectUser(m.id)}
                        className="w-full text-left flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <Avatar name={m.full_name} url={m.avatar_url} />
                        <div>
                          <p className="text-sm font-medium">{m.full_name}</p>
                          <p className="text-xs text-muted-foreground">{m.email}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Conversation */}
          {selectedUserId && !showNewDm && (
            <Card className="flex-1 flex flex-col overflow-hidden">
              {/* Header */}
              <div className="p-4 border-b flex items-center gap-3 shrink-0">
                {selectedUser && (
                  <>
                    <Avatar name={(selectedUser as any).full_name} url={(selectedUser as any).avatar_url} />
                    <div>
                      <p className="font-semibold text-sm">{(selectedUser as any).full_name}</p>
                      <p className="text-xs text-muted-foreground">{(selectedUser as any).email}</p>
                    </div>
                  </>
                )}
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {msgsLoading ? (
                  <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-primary" /></div>
                ) : (
                  <>
                    {(activeConv?.messages ?? []).map((msg: Message) => (
                      <div
                        key={msg.id}
                        className={`flex items-end gap-2 ${msg.is_sent ? 'flex-row-reverse' : 'flex-row'}`}
                      >
                        {!msg.is_sent && activeConv?.user && (
                          <Avatar name={activeConv.user.full_name} url={activeConv.user.avatar_url} size={7} />
                        )}
                        <div className={`max-w-[70%] flex flex-col ${msg.is_sent ? 'items-end' : 'items-start'}`}>
                          <div className={`rounded-2xl px-3 py-2 text-sm ${
                            msg.is_sent
                              ? 'bg-primary text-primary-foreground rounded-br-sm'
                              : 'bg-muted rounded-bl-sm'
                          }`}>
                            <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                          </div>
                          <span className="text-xs text-muted-foreground mt-0.5">
                            {formatRelativeTime(msg.created_at)}
                          </span>
                        </div>
                      </div>
                    ))}
                    <div ref={bottomRef} />
                  </>
                )}
              </div>

              {/* Input */}
              <div className="border-t p-4 shrink-0">
                <div className="flex gap-2">
                  <Input
                    placeholder="Type a message..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                    disabled={sendMutation.isPending}
                  />
                  <Button onClick={handleSend} disabled={!text.trim() || sendMutation.isPending}>
                    {sendMutation.isPending
                      ? <Loader2 className="h-4 w-4 animate-spin" />
                      : <Send className="h-4 w-4" />}
                  </Button>
                </div>
                {sendMutation.isError && (
                  <p className="text-xs text-red-500 mt-1">Failed to send message.</p>
                )}
              </div>
            </Card>
          )}

          {/* Empty state */}
          {!selectedUserId && !showNewDm && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto text-gray-400 mb-3" />
                <p className="text-muted-foreground">Select a conversation or start a new one</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
