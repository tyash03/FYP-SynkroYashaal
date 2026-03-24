'use client'

import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  BarChart3,
  TrendingUp,
  Users,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Target,
  Calendar,
} from 'lucide-react'

export default function AnalyticsPage() {
  const { data: workload, isLoading: workloadLoading } = useQuery({
    queryKey: ['analytics', 'workload'],
    queryFn: async () => {
      const { data } = await api.get('/api/analytics/workload?days=30')
      return data
    },
  })

  const { data: teamWorkload, isLoading: teamLoading } = useQuery({
    queryKey: ['analytics', 'team-workload'],
    queryFn: async () => {
      const { data } = await api.get('/api/analytics/team-workload')
      return data
    },
  })

  const { data: meetingInsights, isLoading: meetingsLoading } = useQuery({
    queryKey: ['analytics', 'meeting-insights'],
    queryFn: async () => {
      const { data } = await api.get('/api/analytics/meeting-insights?days=30')
      return data
    },
  })

  const { data: trend, isLoading: trendLoading } = useQuery({
    queryKey: ['analytics', 'productivity-trend'],
    queryFn: async () => {
      const { data } = await api.get('/api/analytics/productivity-trend?days=14')
      return data
    },
  })

  const isLoading = workloadLoading || teamLoading || meetingsLoading || trendLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Team productivity insights and workload distribution
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Tasks (30d)</p>
                <p className="text-3xl font-bold">{workload?.total_tasks || 0}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-3xl font-bold">{workload?.completed_tasks || 0}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Overdue</p>
                <p className="text-3xl font-bold text-red-600">
                  {workload?.overdue_tasks || 0}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completion Rate</p>
                <p className="text-3xl font-bold">{workload?.completion_rate || 0}%</p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tasks by Status & Priority */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Tasks by Status</CardTitle>
            <CardDescription>Distribution of tasks across statuses (30d)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { key: 'todo', label: 'To Do', color: 'bg-gray-500' },
                { key: 'in_progress', label: 'In Progress', color: 'bg-blue-500' },
                { key: 'done', label: 'Done', color: 'bg-green-500' },
                { key: 'blocked', label: 'Blocked', color: 'bg-red-500' },
              ].map((s) => {
                const count = workload?.tasks_by_status?.[s.key] || 0
                const total = workload?.total_tasks || 1
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={s.key} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{s.label}</span>
                      <span className="text-muted-foreground">
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${s.color}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Tasks by Priority</CardTitle>
            <CardDescription>Distribution of tasks across priorities (30d)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { key: 'urgent', label: 'Urgent', color: 'bg-red-500' },
                { key: 'high', label: 'High', color: 'bg-orange-500' },
                { key: 'medium', label: 'Medium', color: 'bg-yellow-500' },
                { key: 'low', label: 'Low', color: 'bg-gray-400' },
              ].map((p) => {
                const count = workload?.tasks_by_priority?.[p.key] || 0
                const total = workload?.total_tasks || 1
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={p.key} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>{p.label}</span>
                      <span className="text-muted-foreground">
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${p.color}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Team Workload */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Team Workload
          </CardTitle>
          <CardDescription>
            Active task distribution across team members
          </CardDescription>
        </CardHeader>
        <CardContent>
          {teamWorkload?.team_workload?.length > 0 ? (
            <div className="space-y-4">
              {teamWorkload.team_workload.map((member: any) => (
                <div
                  key={member.user_id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                      {member.full_name
                        .split(' ')
                        .map((n: string) => n[0])
                        .join('')
                        .toUpperCase()
                        .slice(0, 2)}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{member.full_name}</p>
                      <p className="text-xs text-muted-foreground">{member.email}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-center">
                      <p className="font-bold">{member.active_tasks}</p>
                      <p className="text-xs text-muted-foreground">Active</p>
                    </div>
                    <div className="text-center">
                      <p className="font-bold text-green-600">
                        {member.completed_tasks_30d}
                      </p>
                      <p className="text-xs text-muted-foreground">Done (30d)</p>
                    </div>
                    {member.overdue_tasks > 0 && (
                      <div className="text-center">
                        <p className="font-bold text-red-600">{member.overdue_tasks}</p>
                        <p className="text-xs text-muted-foreground">Overdue</p>
                      </div>
                    )}
                    <div className="text-center">
                      <p className="font-bold">{member.estimated_hours_remaining}h</p>
                      <p className="text-xs text-muted-foreground">Est. Hours</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No team members found
            </p>
          )}
        </CardContent>
      </Card>

      {/* Meeting Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Meeting Insights (30 days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">{meetingInsights?.total_meetings || 0}</p>
              <p className="text-xs text-muted-foreground">Total Meetings</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">
                {meetingInsights?.total_action_items || 0}
              </p>
              <p className="text-xs text-muted-foreground">Action Items Extracted</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">
                {meetingInsights?.action_item_conversion_rate || 0}%
              </p>
              <p className="text-xs text-muted-foreground">Conversion Rate</p>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <p className="text-2xl font-bold">
                {meetingInsights?.average_duration_minutes
                  ? `${meetingInsights.average_duration_minutes}m`
                  : 'N/A'}
              </p>
              <p className="text-xs text-muted-foreground">Avg Duration</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Productivity Trend */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Productivity Trend (14 days)
          </CardTitle>
          <CardDescription>Tasks created vs completed per day</CardDescription>
        </CardHeader>
        <CardContent>
          {trend?.trend?.length > 0 ? (
            <div className="space-y-2">
              {/* Simple bar chart representation */}
              <div className="flex items-end gap-1 h-32">
                {trend.trend.map((day: any, idx: number) => {
                  const maxVal = Math.max(
                    ...trend.trend.map((d: any) =>
                      Math.max(d.created, d.completed, 1)
                    )
                  )
                  const createdH = (day.created / maxVal) * 100
                  const completedH = (day.completed / maxVal) * 100
                  return (
                    <div
                      key={idx}
                      className="flex-1 flex items-end gap-px"
                      title={`${day.date}: ${day.created} created, ${day.completed} completed`}
                    >
                      <div
                        className="flex-1 bg-blue-300 rounded-t"
                        style={{ height: `${Math.max(createdH, 2)}%` }}
                      />
                      <div
                        className="flex-1 bg-green-400 rounded-t"
                        style={{ height: `${Math.max(completedH, 2)}%` }}
                      />
                    </div>
                  )
                })}
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{trend.trend[0]?.date}</span>
                <span>{trend.trend[trend.trend.length - 1]?.date}</span>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded bg-blue-300" />
                  <span>Created</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="h-3 w-3 rounded bg-green-400" />
                  <span>Completed</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No trend data available yet
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
