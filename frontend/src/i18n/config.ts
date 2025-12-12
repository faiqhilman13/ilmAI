import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  ms: {
    translation: {
      // App
      appName: 'IlmuAI',
      tagline: 'Platform Ilmu Islam untuk Muslim Malaysia',

      // Navigation
      home: 'Utama',
      chat: 'Tanya',
      bookmarks: 'Penanda',
      settings: 'Tetapan',
      login: 'Log Masuk',
      register: 'Daftar',
      logout: 'Log Keluar',

      // Chat
      askQuestion: 'Tanya soalan tentang Islam...',
      send: 'Hantar',
      newChat: 'Perbualan Baru',
      chatHistory: 'Sejarah Perbualan',
      noConversations: 'Tiada perbualan lagi',

      // Citations
      sources: 'Sumber Rujukan',
      quran: 'Al-Quran',
      hadith: 'Hadis',
      fiqh: 'Fiqh',
      fatwa: 'Fatwa',
      viewSource: 'Lihat Sumber',

      // Hadith grading
      sahih: 'Sahih',
      hasan: 'Hasan',
      daif: "Da'if",
      mawdu: "Mawdu'",

      // Auth
      email: 'E-mel',
      password: 'Kata Laluan',
      confirmPassword: 'Sahkan Kata Laluan',
      displayName: 'Nama Paparan',
      forgotPassword: 'Lupa Kata Laluan?',
      noAccount: 'Belum ada akaun?',
      haveAccount: 'Sudah ada akaun?',

      // Settings
      language: 'Bahasa',
      theme: 'Tema',
      light: 'Cerah',
      dark: 'Gelap',
      madhab: 'Mazhab',
      showArabic: 'Paparkan Teks Arab',

      // Errors
      error: 'Ralat',
      networkError: 'Ralat rangkaian. Sila cuba lagi.',
      unauthorized: 'Sesi tamat. Sila log masuk semula.',

      // Common
      loading: 'Memuatkan...',
      save: 'Simpan',
      cancel: 'Batal',
      delete: 'Padam',
      edit: 'Sunting',
      close: 'Tutup',
      confirm: 'Sahkan',

      // Disclaimer
      disclaimer: 'Penafian',
      scholarAdvice: 'Untuk keputusan hukum yang mengikat, sila rujuk ulama atau mufti tempatan.',
    },
  },
  en: {
    translation: {
      // App
      appName: 'IlmuAI',
      tagline: 'Islamic Knowledge Platform for Malaysian Muslims',

      // Navigation
      home: 'Home',
      chat: 'Ask',
      bookmarks: 'Bookmarks',
      settings: 'Settings',
      login: 'Login',
      register: 'Register',
      logout: 'Logout',

      // Chat
      askQuestion: 'Ask a question about Islam...',
      send: 'Send',
      newChat: 'New Chat',
      chatHistory: 'Chat History',
      noConversations: 'No conversations yet',

      // Citations
      sources: 'Reference Sources',
      quran: 'Quran',
      hadith: 'Hadith',
      fiqh: 'Fiqh',
      fatwa: 'Fatwa',
      viewSource: 'View Source',

      // Hadith grading
      sahih: 'Sahih (Authentic)',
      hasan: 'Hasan (Good)',
      daif: "Da'if (Weak)",
      mawdu: "Mawdu' (Fabricated)",

      // Auth
      email: 'Email',
      password: 'Password',
      confirmPassword: 'Confirm Password',
      displayName: 'Display Name',
      forgotPassword: 'Forgot Password?',
      noAccount: "Don't have an account?",
      haveAccount: 'Already have an account?',

      // Settings
      language: 'Language',
      theme: 'Theme',
      light: 'Light',
      dark: 'Dark',
      madhab: 'Madhab',
      showArabic: 'Show Arabic Text',

      // Errors
      error: 'Error',
      networkError: 'Network error. Please try again.',
      unauthorized: 'Session expired. Please login again.',

      // Common
      loading: 'Loading...',
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      close: 'Close',
      confirm: 'Confirm',

      // Disclaimer
      disclaimer: 'Disclaimer',
      scholarAdvice: 'For binding religious rulings, please consult local scholars or muftis.',
    },
  },
}

i18n.use(initReactI18next).init({
  resources,
  lng: 'ms', // Default to Malay
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
