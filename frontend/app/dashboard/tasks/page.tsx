'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { taskApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Search, Filter } from 'lucide-react'
import { formatDueDate, getStatusColor, getPriorityColor, capitalize } from '@/lib/utils'
import type { Task } from '@/types'
import { CreateTaskDialog } from '@/components/create-task-dialog'

export default function TasksPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')

  // Fetch tasks
  const { data, isLoading } = useQuery<{ data: Task[] }>({
    queryKey: ['tasks', statusFilter, priorityFilter],
    queryFn: () => {
      const params: any = { limit: 50 }
      if (statusFilter !== 'all') params.status = statusFilter
      if (priorityFilter !== 'all') params.priority = priorityFilter
      return taskApi.getTasks(params)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => taskApi.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['task-stats'] })
    },
  })

  // Update task status
  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      taskApi.updateTask(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['task-stats'] })
    },
  })

  const tasks = data?.data || []

  // Filter by search term
  const filteredTasks = tasks.filter((task) =>
    task.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tasks</h1>
          <p className="text-sm text-muted-foreground">
            Manage and track your team's tasks
          </p>
        </div>
        <CreateTaskDialog />
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search tasks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="all">All Status</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
            <option value="blocked">Blocked</option>
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="all">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          {/* Results count */}
          <div className="flex items-center text-sm text-muted-foreground">
            <Filter className="h-4 w-4 mr-2" />
            {filteredTasks.length} tasks
          </div>
        </div>
      </Card>

      {/* Tasks List */}
      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading tasks...</p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-muted-foreground mb-4">No tasks found</p>
          <CreateTaskDialog />
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((task) => (
            <Card key={task.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                {/* Status checkbox */}
                <input
                  type="checkbox"
                  checked={task.status === 'done'}
                  onChange={() => {
                    const newStatus = task.status === 'done' ? 'todo' : 'done'
                    updateStatusMutation.mutate({ id: task.id, status: newStatus })
                  }}
                  className="mt-1 h-4 w-4 rounded border-gray-300"
                />

                {/* Task details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className={`font-medium ${task.status === 'done' ? 'line-through text-muted-foreground' : ''}`}>
                      {task.title}
                    </h3>
                    <div className="flex gap-2 flex-shrink-0">
                      <Badge className={getStatusColor(task.status)}>
                        {capitalize(task.status.replace('_', ' '))}
                      </Badge>
                      <Badge className={getPriorityColor(task.priority)}>
                        {capitalize(task.priority)}
                      </Badge>
                    </div>
                  </div>

                  {task.description && (
                    <p className="text-sm text-muted-foreground mb-2 line-clamp-2">
                      {task.description}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                    {task.assignee && (
                      <span>Assigned to: {task.assignee.full_name}</span>
                    )}
                    {task.due_date && (
                      <span>Due: {formatDueDate(task.due_date)}</span>
                    )}
                    {task.estimated_hours && (
                      <span>{task.estimated_hours}h estimated</span>
                    )}
                    <span className="capitalize">Source: {task.source_type}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm('Delete this task?')) {
                        deleteMutation.mutate(task.id)
                      }
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
