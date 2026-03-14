import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { DatabasePage } from './pages/DatabasePage'
import { StrictMode } from 'react'
import { Layout } from './components/Layout'
import { ChatProvider } from './contexts/ChatContext'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <HomePage />
      },
      {
        path: 'database',
        element: <DatabasePage />
      }
    ]
  }
])

function App() {
  return (
    <StrictMode>
      <ChatProvider>
        <RouterProvider router={router} />
      </ChatProvider>
    </StrictMode>
  )
}

export default App
