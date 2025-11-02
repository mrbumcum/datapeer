import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { DatabasePage } from './pages/DatabasePage'
import { StrictMode } from 'react'
import { Layout } from './components/Layout'

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
      <RouterProvider router={router} />
    </StrictMode>
  )
}

export default App
