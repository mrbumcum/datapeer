import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function Layout() {
  return (
    <div className="h-screen flex">
      <Sidebar />
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}

