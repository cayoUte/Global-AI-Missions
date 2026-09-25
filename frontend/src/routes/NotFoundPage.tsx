import { Link } from 'react-router'

import { Backdrop } from '../components/Backdrop'
import { buttonClasses } from '../components/buttonClasses'
import { useMe } from '../features/auth/session'

export function NotFoundPage() {
  const me = useMe()
  const student = me.data?.role === 'student'
  const home = me.data ? (student ? '/world' : '/teacher') : '/check-in'
  return (
    <div className="relative min-h-dvh">
      <div className="fixed inset-0">
        <Backdrop backdropKey="platform_empty" />
      </div>
      <main className="relative z-10 mx-auto max-w-reading space-y-6 px-4 pt-[30vh]">
        <h1 className="font-display text-3xl font-semibold">This platform doesn&apos;t exist.</h1>
        <Link to={home} className={buttonClasses('primary', 'lg')}>
          {me.data ? (student ? 'Back to the English World' : 'Back') : 'Check in'}
        </Link>
      </main>
    </div>
  )
}
