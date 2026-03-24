'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { messagesApi } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  MessageSquare,
  Send,
  Loader2,
  ArrowLeft,
  User,
  Search,
  X,
} from 'lucide-react'
import { formatRelativeTime } from '@/lib/utils'
import Link from 'next/link'

interface DmMessage {
  id: string
  sender_name: string | null
  content: string
  timestamp: string | null
  intent: string | null
  direction?: 'sent' | 'received'
}

interface Conversation {
  channel_id: string | null
  channel_type: string | null
  sender_name: string | null
  last_message: string
  last_timestamp: string | null
  messages: DmMessage[]
}

interface SlackUser {
  id: string
  name: string
  real_name: string | null
  avatar: string | null
}

const INTENT_COLORS: Record<string, string> = {
  task_request: 'bg-blue-100 text-blue-800',
  blocker: 'bg-red-100 text-red-800',
  urgent_issue: 'bg-orange-100 text-orange-800',
  question: 'bg-purple-100 text-purple-800',
  information: 'bg-gray-100 text-gray-700',
  casual: 'bg-green-100 text-green-800',
}

export default function SlackDmsPage() {
  const queryClient = useQueryClient()
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null)
  const [composing, setComposing] = useState(false)
  const [newDmUser, setNewDmUser] = useState<SlackUser | null>(null)
  const [messageText, setMessageText] = useState('')
  const [userSearch, setUserSearch] = useState('')

  // DM conversations
  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ['dm-conversations'],
    queryFn: async () => (await messagesApi.getDmConversations()).data as Conversation[],
    refetchInterval: 10000,
  })

  // Always derive from latest query data so new messages appear immediately
  const selectedConv = selectedChannelId
    ? conversations.find(c => c.channel_id === selectedChannelId) ?? null
    : null

  // Workspace users (for composing new DM)
  const { data: slackUsers = [], isLoading: usersLoading } = useQuery({
    queryKey: ['slack-users'],
    queryFn: async () => (await messagesApi.getSlackUsers()).data as SlackUser[],
    enabled: composing,
  })

  const sendMutation = useMutation({
    mutationFn: (payload: { slack_user_id: string; message: string; channel_id?: string }) =>
      messagesApi.sendDm(payload),
    onSuccess: (response) => {
      setMessageText('')
      setNewDmUser(null)
      setComposing(false)
      const channelId = response.data?.channel_id
      if (channelId) setSelectedChannelId(channelId)
      queryClient.invalidateQueries({ queryKey: ['dm-conversations'] })
    },
  })

  const handleSend = () => {
    if (!messageText.trim()) return
    const userId = newDmUser?.id || ''
    const channelId = selectedConv?.channel_id || undefined
    if (!userId && !channelId) return

    sendMutation.mutate({
      slack_user_id: userId,
      message: messageText.trim(),
      channel_id: channelId,
    })
  }

  const filteredUsers = slackUsers.filter((u) =>
    u.name?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.real_name?.toLowerCase().includes(userSearch.toLowerCase())
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard/slack">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Slack
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Direct Messages</h1>
            <p className="text-sm text-muted-foreground">
              Slack DMs synced to your workspace
            </p>
          </div>
        </div>
        <Button onClick={() => { setComposing(true); setSelectedChannelId(null) }}>
          <MessageSquare className="h-4 w-4 mr-2" />
          New DM
        </Button>
      </div>

      <div className="flex gap-4 h-[calc(100vh-14rem)]">
        {/* Conversation list */}
        <div className="w-72 shrink-0 flex flex-col gap-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : conversations.length === 0 ? (
            <Card className="p-6 text-center">
              <MessageSquare className="h-8 w-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-muted-foreground">No DMs yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Send a DM in Slack or start one here.
              </p>
            </Card>
          ) : (
            <Card className="overflow-hidden">
              <CardContent className="p-0 divide-y">
                {conversations.map((conv, idx) => (
                  <button
                    key={conv.channel_id || idx}
                    className={`w-full text-left px-3 py-3 hover:bg-muted/50 transition-colors flex items-start gap-3 ${
                      selectedConv?.channel_id === conv.channel_id ? 'bg-primary/10' : ''
                    }`}
                    onClick={() => { setSelectedChannelId(conv.channel_id); setComposing(false) }}
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#4A154B] text-white text-xs font-bold mt-0.5">
                      {conv.sender_name ? conv.sender_name.slice(0, 2).toUpperCase() : <User className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold truncate">
                        {conv.sender_name || 'Unknown'}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">{conv.last_message}</p>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap shrink-0 mt-0.5">
                      {conv.last_timestamp ? formatRelativeTime(conv.last_timestamp) : ''}
                    </span>
                  </button>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right panel */}
        <div className="flex-1 flex flex-col">
          {/* New DM compose */}
          {composing && (
            <Card className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b flex items-center justify-between">
                <h2 className="font-semibold">New Direct Message</h2>
                <button onClick={() => setComposing(false)}>
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>

              {/* User picker */}
              {!newDmUser ? (
                <div className="p-4 flex-1">
                  <div className="relative mb-3">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search workspace members..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  {usersLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    </div>
                  ) : (
                    <div className="space-y-1 overflow-y-auto max-h-80">
                      {filteredUsers.map((u) => (
                        <button
                          key={u.id}
                          className="w-full text-left flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors"
                          onClick={() => setNewDmUser(u)}
                        >
                          {u.avatar ? (
                            <img src={u.avatar} alt={u.name} className="h-8 w-8 rounded-full" />
                          ) : (
                            <div className="h-8 w-8 rounded-full bg-[#4A154B] flex items-center justify-center text-white text-xs font-bold">
                              {u.name?.slice(0, 2).toUpperCase()}
                            </div>
                          )}
                          <div>
                            <p className="text-sm font-medium">{u.real_name || u.name}</p>
                            <p className="text-xs text-muted-foreground">@{u.name}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <div className="flex-1 p-4 flex flex-col">
                    <div className="flex items-center gap-2 mb-4 p-3 bg-muted/50 rounded-lg">
                      {newDmUser.avatar ? (
                        <img src={newDmUser.avatar} alt={newDmUser.name} className="h-8 w-8 rounded-full" />
                      ) : (
                        <div className="h-8 w-8 rounded-full bg-[#4A154B] flex items-center justify-center text-white text-xs font-bold">
                          {newDmUser.name?.slice(0, 2).toUpperCase()}
                        </div>
                      )}
                      <div className="flex-1">
                        <p className="text-sm font-medium">{newDmUser.real_name || newDmUser.name}</p>
                        <p className="text-xs text-muted-foreground">@{newDmUser.name}</p>
                      </div>
                      <button onClick={() => setNewDmUser(null)} className="text-muted-foreground hover:text-foreground">
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    <p className="text-sm text-muted-foreground text-center flex-1 flex items-center justify-center">
                      Start a new conversation with {newDmUser.real_name || newDmUser.name}
                    </p>
                  </div>
                  <div className="border-t p-4">
                    <div className="flex gap-2">
                      <Input
                        placeholder={`Message ${newDmUser.real_name || newDmUser.name}...`}
                        value={messageText}
                        onChange={(e) => setMessageText(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                        disabled={sendMutation.isPending}
                      />
                      <Button
                        onClick={handleSend}
                        disabled={!messageText.trim() || sendMutation.isPending}
                      >
                        {sendMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    {sendMutation.isError && (
                      <p className="text-xs text-red-500 mt-1">Failed to send. Make sure Slack is connected and the bot has DM permissions.</p>
                    )}
                  </div>
                </>
              )}
            </Card>
          )}

          {/* Conversation view */}
          {selectedConv && !composing && (
            <Card className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-[#4A154B] flex items-center justify-center text-white text-xs font-bold">
                  {selectedConv.sender_name?.slice(0, 2).toUpperCase() || '??'}
                </div>
                <div>
                  <p className="font-semibold text-sm">{selectedConv.sender_name || 'Unknown'}</p>
                  <p className="text-xs text-muted-foreground">Slack DM</p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {[...selectedConv.messages].reverse().map((msg) => {
                  const isSent = msg.direction === 'sent'
                  return (
                    <div key={msg.id} className={`flex items-end gap-2 ${isSent ? 'flex-row-reverse' : 'flex-row'}`}>
                      {!isSent && (
                        <div className="h-7 w-7 shrink-0 rounded-full bg-[#4A154B] flex items-center justify-center text-white text-xs font-bold">
                          {msg.sender_name?.slice(0, 2).toUpperCase() || '?'}
                        </div>
                      )}
                      <div className={`max-w-[70%] ${isSent ? 'items-end' : 'items-start'} flex flex-col`}>
                        {!isSent && (
                          <span className="text-xs font-semibold text-muted-foreground mb-0.5">{msg.sender_name}</span>
                        )}
                        <div className={`rounded-2xl px-3 py-2 text-sm ${isSent ? 'bg-primary text-white rounded-br-sm' : 'bg-muted rounded-bl-sm'}`}>
                          <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                        </div>
                        <span className="text-xs text-muted-foreground mt-0.5">
                          {msg.timestamp ? formatRelativeTime(msg.timestamp) : ''}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Reply box */}
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <Input
                    placeholder={`Reply to ${selectedConv.sender_name || 'Unknown'}...`}
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
                    disabled={sendMutation.isPending}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!messageText.trim() || sendMutation.isPending}
                  >
                    {sendMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                {sendMutation.isError && (
                  <p className="text-xs text-red-500 mt-1">Failed to send message.</p>
                )}
              </div>
            </Card>
          )}

          {/* Empty state */}
          {!selectedConv && !composing && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="h-12 w-12 mx-auto text-gray-400 mb-3" />
                <p className="text-muted-foreground">Select a conversation or start a new DM</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
