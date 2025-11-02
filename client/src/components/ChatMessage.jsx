import robotIcon from '../assets/robot-svgrepo-com.svg'
import userIcon from '../assets/user-svgrepo-com.svg'

export function ChatMessage({ message, isUser = false }) {
  return (
    <div className={`flex items-start gap-3 mb-6 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-10 h-10 rounded-full ${isUser ? 'bg-purple-200' : 'bg-gray-200'} flex items-center justify-center`}>
        <img 
          src={isUser ? userIcon : robotIcon} 
          alt={isUser ? 'User' : 'AI'} 
          className="w-6 h-6"
        />
      </div>
      
      {/* Message content */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-3xl`}>
        <div className={`rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-purple-100 text-gray-800' 
            : 'bg-white text-gray-800'
        } shadow-sm`}>
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
            {message}
          </p>
        </div>
        
        {/* Interactive icons for AI messages */}
        {!isUser && (
          <div className="flex items-center gap-3 mt-2">
            <button className="text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 12h.01M16 12h.01" />
              </svg>
            </button>
            <button className="text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
            </button>
            <button className="text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-5 h-5 transform rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
