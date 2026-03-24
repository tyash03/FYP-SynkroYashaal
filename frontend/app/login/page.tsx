'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/stores/authStore'
import { authApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

type LoginView = 'login' | 'forgot' | 'reset'

export default function LoginPage() {
  const router = useRouter()
  const { login, isLoading, error, clearError } = useAuthStore()

  const [view, setView] = useState<LoginView>('login')

  // Login state
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  // Forgot password state
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotMessage, setForgotMessage] = useState('')
  const [forgotError, setForgotError] = useState('')
  const [resetToken, setResetToken] = useState('')

  // Reset password state
  const [resetTokenInput, setResetTokenInput] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmNewPassword, setConfirmNewPassword] = useState('')
  const [resetLoading, setResetLoading] = useState(false)
  const [resetMessage, setResetMessage] = useState('')
  const [resetError, setResetError] = useState('')

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()

    try {
      await login({ email, password })
      router.push('/dashboard')
    } catch (err) {
      // Error is handled in store
    }
  }

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setForgotLoading(true)
    setForgotError('')
    setForgotMessage('')

    try {
      const res = await authApi.forgotPassword(forgotEmail)
      const data = res.data
      setForgotMessage(data.message)

      // If token is returned (dev mode), auto-fill it
      if (data.reset_token) {
        setResetToken(data.reset_token)
        setResetTokenInput(data.reset_token)
      }
    } catch (err: any) {
      setForgotError(err.response?.data?.detail || 'Failed to process request')
    } finally {
      setForgotLoading(false)
    }
  }

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResetError('')
    setResetMessage('')

    if (newPassword !== confirmNewPassword) {
      setResetError('Passwords do not match')
      return
    }

    if (newPassword.length < 8) {
      setResetError('Password must be at least 8 characters')
      return
    }

    setResetLoading(true)

    try {
      const res = await authApi.resetPassword(resetTokenInput, newPassword)
      setResetMessage(res.data.message)
      // Redirect to login after 2 seconds
      setTimeout(() => {
        setView('login')
        setResetMessage('')
        setResetTokenInput('')
        setNewPassword('')
        setConfirmNewPassword('')
      }, 2500)
    } catch (err: any) {
      setResetError(err.response?.data?.detail || 'Failed to reset password')
    } finally {
      setResetLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-3xl font-bold text-center">Synkro</CardTitle>
          <CardDescription className="text-center">
            {view === 'login' && 'AI-Powered Workspace'}
            {view === 'forgot' && 'Reset your password'}
            {view === 'reset' && 'Enter new password'}
          </CardDescription>
        </CardHeader>

        {/* LOGIN VIEW */}
        {view === 'login' && (
          <form onSubmit={handleLoginSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <button
                    type="button"
                    onClick={() => { clearError(); setView('forgot') }}
                    className="text-xs text-primary hover:underline"
                  >
                    Forgot password?
                  </button>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>

              <p className="text-center text-sm text-gray-600">
                Don&apos;t have an account?{' '}
                <Link href="/register" className="font-medium text-primary hover:underline">
                  Sign up
                </Link>
              </p>
            </CardFooter>
          </form>
        )}

        {/* FORGOT PASSWORD VIEW */}
        {view === 'forgot' && (
          <form onSubmit={handleForgotSubmit}>
            <CardContent className="space-y-4">
              {forgotError && (
                <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                  {forgotError}
                </div>
              )}

              {forgotMessage && (
                <div className="rounded-md bg-green-50 p-3 text-sm text-green-800 space-y-2">
                  <p>{forgotMessage}</p>
                  {resetToken && (
                    <div className="mt-2">
                      <p className="font-medium text-xs">Your reset code (copy this):</p>
                      <code className="block bg-green-100 rounded p-2 text-xs break-all mt-1">
                        {resetToken}
                      </code>
                      <Button
                        type="button"
                        size="sm"
                        className="mt-2 w-full"
                        onClick={() => setView('reset')}
                      >
                        Continue to Reset Password
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {!forgotMessage && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Enter your email address and we&apos;ll generate a reset code for you.
                  </p>
                  <Label htmlFor="forgotEmail">Email Address</Label>
                  <Input
                    id="forgotEmail"
                    type="email"
                    placeholder="you@example.com"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                    disabled={forgotLoading}
                  />
                </div>
              )}
            </CardContent>

            <CardFooter className="flex flex-col space-y-3">
              {!forgotMessage && (
                <Button type="submit" className="w-full" disabled={forgotLoading}>
                  {forgotLoading ? 'Processing...' : 'Get Reset Code'}
                </Button>
              )}

              <button
                type="button"
                onClick={() => { setView('login'); setForgotMessage(''); setForgotError(''); setResetToken('') }}
                className="text-sm text-primary hover:underline"
              >
                Back to Sign In
              </button>

              {forgotMessage && (
                <button
                  type="button"
                  onClick={() => setView('reset')}
                  className="text-sm text-primary hover:underline"
                >
                  I have a reset code
                </button>
              )}
            </CardFooter>
          </form>
        )}

        {/* RESET PASSWORD VIEW */}
        {view === 'reset' && (
          <form onSubmit={handleResetSubmit}>
            <CardContent className="space-y-4">
              {resetError && (
                <div className="rounded-md bg-red-50 p-3 text-sm text-red-800">
                  {resetError}
                </div>
              )}

              {resetMessage && (
                <div className="rounded-md bg-green-50 p-3 text-sm text-green-800">
                  {resetMessage} Redirecting to login...
                </div>
              )}

              {!resetMessage && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="resetToken">Reset Code</Label>
                    <Input
                      id="resetToken"
                      type="text"
                      placeholder="Paste your reset code here"
                      value={resetTokenInput}
                      onChange={(e) => setResetTokenInput(e.target.value)}
                      required
                      disabled={resetLoading}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <Input
                      id="newPassword"
                      type="password"
                      placeholder="••••••••"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      disabled={resetLoading}
                      minLength={8}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmNewPassword">Confirm New Password</Label>
                    <Input
                      id="confirmNewPassword"
                      type="password"
                      placeholder="••••••••"
                      value={confirmNewPassword}
                      onChange={(e) => setConfirmNewPassword(e.target.value)}
                      required
                      disabled={resetLoading}
                    />
                  </div>
                </>
              )}
            </CardContent>

            <CardFooter className="flex flex-col space-y-3">
              {!resetMessage && (
                <Button type="submit" className="w-full" disabled={resetLoading}>
                  {resetLoading ? 'Resetting...' : 'Reset Password'}
                </Button>
              )}

              <button
                type="button"
                onClick={() => { setView('forgot'); setResetError(''); setResetMessage('') }}
                className="text-sm text-primary hover:underline"
              >
                Back
              </button>
            </CardFooter>
          </form>
        )}
      </Card>
    </div>
  )
}
