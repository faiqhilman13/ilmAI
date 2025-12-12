import { useTranslation } from 'react-i18next'
import { Sparkles } from 'lucide-react'

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void
}

const SUGGESTED_QUESTIONS = {
  ms: [
    {
      question: 'Bagaimana cara solat yang betul?',
      icon: '🕌',
    },
    {
      question: 'Apakah rukun Islam?',
      icon: '☪️',
    },
    {
      question: 'Apakah perkara yang membatalkan puasa?',
      icon: '🌙',
    },
    {
      question: 'Bagaimana cara mengira zakat pendapatan?',
      icon: '💰',
    },
    {
      question: 'Apakah syarat sah wuduk?',
      icon: '💧',
    },
    {
      question: 'Bagaimana hukum solat sunat tahajjud?',
      icon: '🌃',
    },
  ],
  en: [
    {
      question: 'What is the correct way to pray?',
      icon: '🕌',
    },
    {
      question: 'What are the pillars of Islam?',
      icon: '☪️',
    },
    {
      question: 'What things invalidate fasting?',
      icon: '🌙',
    },
    {
      question: 'How to calculate income zakat?',
      icon: '💰',
    },
    {
      question: 'What are the conditions for valid ablution?',
      icon: '💧',
    },
    {
      question: 'What is the ruling on tahajjud prayer?',
      icon: '🌃',
    },
  ],
}

export default function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  const { i18n } = useTranslation()
  const questions = SUGGESTED_QUESTIONS[i18n.language as 'ms' | 'en'] || SUGGESTED_QUESTIONS.ms

  return (
    <div>
      <div className="flex items-center justify-center gap-2 text-sm text-gray-500 mb-4">
        <Sparkles className="w-4 h-4" />
        <span>
          {i18n.language === 'ms' ? 'Soalan cadangan' : 'Suggested questions'}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {questions.map((item, index) => (
          <button
            key={index}
            onClick={() => onSelect(item.question)}
            className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors text-left group"
          >
            <span className="text-2xl">{item.icon}</span>
            <span className="text-sm text-gray-700 group-hover:text-primary-700">
              {item.question}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
