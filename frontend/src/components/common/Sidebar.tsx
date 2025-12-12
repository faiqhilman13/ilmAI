import { useTranslation } from 'react-i18next'
import { Plus, MessageCircle, X, Trash2 } from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'
import { useAuthStore } from '../../stores/authStore'

interface SidebarProps {
  onClose: () => void
}

export default function Sidebar({ onClose }: SidebarProps) {
  const { t } = useTranslation()
  const { clearMessages, currentConversation } = useChatStore()
  const { isAuthenticated } = useAuthStore()

  // Mock conversations for now
  const conversations = [
    { id: '1', title: 'Soalan tentang solat', date: 'Hari ini' },
    { id: '2', title: 'Hukum puasa', date: 'Semalam' },
    { id: '3', title: 'Zakat fitrah', date: '3 hari lepas' },
  ]

  const handleNewChat = () => {
    clearMessages()
    onClose()
  }

  return (
    <div className="h-full bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="font-semibold">{t('chatHistory')}</h2>
        <button
          onClick={onClose}
          className="lg:hidden p-1 hover:bg-gray-700 rounded"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* New chat button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>{t('newChat')}</span>
        </button>
      </div>

      {/* Conversations list */}
      <div className="flex-1 overflow-y-auto px-3">
        {isAuthenticated ? (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left hover:bg-gray-800 transition-colors group ${
                  currentConversation?.id === conv.id ? 'bg-gray-800' : ''
                }`}
              >
                <MessageCircle className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{conv.title}</p>
                  <p className="text-xs text-gray-500">{conv.date}</p>
                </div>
                <button
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-600 rounded"
                  onClick={(e) => {
                    e.stopPropagation()
                    // Handle delete
                  }}
                >
                  <Trash2 className="w-4 h-4 text-gray-400" />
                </button>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">Log masuk untuk menyimpan perbualan</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700 text-center text-xs text-gray-500">
        <p>IlmuAI v0.1.0</p>
        <p className="mt-1">Platform Ilmu Islam untuk Muslim Malaysia</p>
      </div>
    </div>
  )
}
