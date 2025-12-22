
import { useEffect, useMemo, useState, useRef, useCallback } from 'react'
import TurkeyMap from '../components/TurkeyMap'
import { LineChart, Line, PieChart, Pie, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts'
import { fetchAnomalies, fetchCityRanking, type AnomalyItem, type RankingResponse } from '../utils/api'
import { getCityNameFromCode } from '../utils/cityMapping'
import DateSelector from '../components/DateSelector'
import { supabase } from '../supabaseClient'


type FilterCategory = {
  label: string
  displayName: string
  icon: string
}

export default function Dashboard() {
  const [dark, setDark] = useState(false) // Default Light Mode

  // ... (lines skipped)


  const [datePickerOpen, setDatePickerOpen] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [tempStartDate, setTempStartDate] = useState('') // Geçici state
  const [tempEndDate, setTempEndDate] = useState('')     // Geçici state
  const [filterOpen, setFilterOpen] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [selectedCity, setSelectedCity] = useState<{ id: string, name: string } | null>(null)
  const [anomalyData, setAnomalyData] = useState<AnomalyItem[]>([])
  const [allCategoriesData, setAllCategoriesData] = useState<Record<string, AnomalyItem[]>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rankingData, setRankingData] = useState<RankingResponse | null>(null)
  const chartsSectionRef = useRef<HTMLElement>(null)

  // Contact form state
  const [contactFormOpen, setContactFormOpen] = useState(false)
  const [contactSubject, setContactSubject] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [contactMessage, setContactMessage] = useState('')
  const [contactSending, setContactSending] = useState(false)

  const filterCategories: FilterCategory[] = [
    { label: 'aydinlatma', displayName: 'Aydınlatma', icon: '/light-bulb.png' },
    { label: 'mesken', displayName: 'Mesken', icon: '/house.png' },
    { label: 'ticarethane', displayName: 'Ticarethane', icon: '/dollar.png' },
    { label: 'sanayi', displayName: 'Sanayi', icon: '/factory.png' },
    { label: 'tarimsal', displayName: 'Tarımsal', icon: '/wheat.png' },
    { label: 'genel', displayName: 'Genel', icon: '/all.png' },
    { label: 'diger', displayName: 'Diğer', icon: '/ellipsis.png' },
  ]

  useEffect(() => {
    const saved = localStorage.getItem('elektraize-theme')
    const isDark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
    setDark(isDark)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    if (dark) {
      root.classList.add('dark')
      localStorage.setItem('elektraize-theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('elektraize-theme', 'light')
    }
  }, [dark])

  // Auto-fill email from user session
  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (user?.email) {
        setContactEmail(user.email)
      }
    }
    getUser()
  }, [])

  // Body class toggling for global styles (like map tooltips)
  useEffect(() => {
    if (dark) {
      document.body.classList.remove('light-mode')
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
      document.body.classList.add('light-mode')
    }
  }, [dark])

  // Modal dışına tıklandığında kapat
  useEffect(() => {
    if (!datePickerOpen) return
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.date-picker-container')) {
        setDatePickerOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [datePickerOpen])

  // TÜM Kategorilerin verisini çek (Sektörel Pasta Grafikleri için)
  const fetchAllCategoriesData = useCallback(async (cityName: string, startDate?: string, endDate?: string) => {
    try {
      console.log(`%c[SÜREÇ] Tüm Kategori Verileri İstendi(${cityName})`, 'color: orange;')
      const categories = ['mesken', 'ticarethane', 'sanayi', 'aydinlatma', 'tarimsal', 'diger']
      const allData: Record<string, AnomalyItem[]> = {}

      await Promise.all(
        categories.map(async (category) => {
          try {
            const data = await fetchAnomalies(
              cityName,
              category, // Kategori fix
              startDate || undefined,
              endDate || undefined
            )
            allData[category] = data
          } catch (err) {
            console.warn(`⚠️ ${category} kategorisi yüklenemedi: `, err)
            allData[category] = []
          }
        })
      )

      setAllCategoriesData(allData)
      console.log(`%c[SÜREÇ] Tüm Kategoriler Çekildi: `, 'color: orange;', Object.keys(allData).join(', '))
    } catch (err) {
      console.error('❌ Kategori verileri yüklenirken hata:', err)
    }
  }, [])

  // Backend'den veri çekme fonksiyonu (seçilen kategori için)
  const fetchCityData = useCallback(async () => {
    // KATI KURAL: Şehir, Sektör, Başlangıç ve Bitiş Tarihi ZORUNLU
    if (!selectedCity || !selectedFilter || !startDate || !endDate) {
      console.log('%c[BEKLENİYOR] Grafik güncellemesi için tüm alanlar (Şehir, Sektör, Tarih Aralığı) doldurulmalı.', 'color: gray;')
      return
    }

    const cityName = getCityNameFromCode(selectedCity.id)
    if (!cityName) {
      setError(`Şehir kodu bulunamadı: ${selectedCity.id} `)
      return
    }

    setLoading(true)
    setError(null)

    try {
      console.log('🔄 API isteği gönderiliyor...', {
        city: cityName,
        category: selectedFilter || 'genel',
        startDate,
        endDate
      })

      const data = await fetchAnomalies(
        cityName,
        selectedFilter || 'genel',
        startDate || undefined,
        endDate || undefined
      )

      console.log('✅ API yanıtı alındı:', data.length, 'kayıt')
      console.log('✅ API yanıtı alındı:', data.length, 'kayıt')
      setAnomalyData(data)

      // Sıralama verisini çek
      try {
        const rankRes = await fetchCityRanking(
          cityName,
          selectedFilter || 'genel',
          startDate || undefined,
          endDate || undefined
        )
        setRankingData(rankRes)
      } catch (e) {
        console.warn('Sıralama verisi alınamadı:', e)
        setRankingData(null)
      }

      // TÜM kategoriler için veri çekme işlemi buradan kaldırıldı (optimize edildi)
      // fetchAllCategoriesData(cityName, startDate, endDate)

      // Grafiklere scroll yap (Header'ı kapatmayacak şekilde offsetli)
      setTimeout(() => {
        if (chartsSectionRef.current) {
          const yOffset = -45; // Header payı
          const element = chartsSectionRef.current;
          const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
          window.scrollTo({ top: y, behavior: 'smooth' });
        }
      }, 300)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bilinmeyen hata'
      console.error('❌ API hatası:', errorMessage)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [selectedCity, selectedFilter, startDate, endDate, fetchAllCategoriesData])

  // Şehir, filtre veya tarih değiştiğinde veri çek (ANA GRAFİK ve SIRALAMA)
  useEffect(() => {
    if (selectedCity) {
      if (startDate && endDate) {
        fetchCityData()
      }
    }
  }, [selectedCity, selectedFilter, startDate, endDate, fetchCityData])

  // SADECE Şehir veya Tarih değiştiğinde PASTA Grafikleri için veri çek (Filtreden BAĞIMSIZ)
  useEffect(() => {
    if (selectedCity && startDate && endDate) {
      const cityName = getCityNameFromCode(selectedCity.id)
      if (cityName) {
        fetchAllCategoriesData(cityName, startDate, endDate)
      }
    }
  }, [selectedCity, startDate, endDate, fetchAllCategoriesData])

  // 1. ANA GRAFİK: Aylık Tüketim (Gerçek vs Tahmin) - Fark fazlaysa kırmızı nokta
  const monthlyMainData = useMemo(() => {
    if (anomalyData.length === 0) return []

    // Gelen verideki mevcut tarihleri (Ay Yıl) topla
    const monthlyGroups: Record<string, { tahmin: number[], gercek: number[], dateObj: Date }> = {}

    anomalyData.forEach((item) => {
      const date = new Date(item.donem)
      // Key olarak "YYYY-MM" kullanalım ki sıralama kolay olsun
      const key = `${date.getFullYear()} -${String(date.getMonth() + 1).padStart(2, '0')} `

      if (!monthlyGroups[key]) {
        monthlyGroups[key] = { tahmin: [], gercek: [], dateObj: date }
      }
      monthlyGroups[key].tahmin.push(item.tahmin / 1000) // MWh
      monthlyGroups[key].gercek.push(item.gercek / 1000) // MWh
    })

    // Grupları array'e çevir ve analiz yap
    return Object.entries(monthlyGroups)
      .map(([key, data]) => {
        const tahmin = Math.round(data.tahmin.reduce((a, b) => a + b, 0) / data.tahmin.length)
        const gerçek = Math.round(data.gercek.reduce((a, b) => a + b, 0) / data.gercek.length)
        const fark = gerçek - tahmin
        const farkYüzdesi = tahmin !== 0 ? Math.abs(fark / tahmin) * 100 : 0

        // Gösterim adı (Örn: Oca 2023) - Manuel formatlama (Browser locale sorunlarını önlemek için)
        const trMonths = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
        const monthIndex = data.dateObj.getMonth()
        const year = data.dateObj.getFullYear()
        const displayMonth = `${trMonths[monthIndex]} ${year} `

        return {
          ay: displayMonth, // Grafik X ekseni
          rawDate: key,     // Sıralama için
          tahmin,
          gerçek,
          fark,
          yüksekFark: farkYüzdesi > 15
        }
      })
      .sort((a, b) => a.rawDate.localeCompare(b.rawDate)) // Kronolojik sırala
  }, [anomalyData])

  // 2. GÜNLÜK TÜKETİM: Saatlik ortalama (0-23 saat)
  const dailyConsumptionData = useMemo(() => {
    if (anomalyData.length === 0) {
      // Placeholder: 24 saatlik örnek veri
      return Array.from({ length: 24 }, (_, i) => ({
        saat: `${i}:00`,
        tüketim: Math.round(50 + Math.random() * 30)
      }))
    }

    // Saatlere göre grupla ve ortalama al
    const hourlyData: Record<number, number[]> = {}

    anomalyData.forEach((item) => {
      const date = new Date(item.donem)
      const hour = date.getHours()
      const consumption = item.gercek / 1000 // MWh'ye çevir

      if (!hourlyData[hour]) {
        hourlyData[hour] = []
      }
      hourlyData[hour].push(consumption)
    })

    // Her saat için ortalama hesapla
    return Array.from({ length: 24 }, (_, hour) => {
      const values = hourlyData[hour] || []
      const average = values.length > 0
        ? Math.round(values.reduce((a, b) => a + b, 0) / values.length)
        : 0

      return {
        saat: `${hour}:00`,
        tüketim: average
      }
    })
  }, [anomalyData])

  // 3. SEKTÖREL DAĞILIM PASTA (Büyük)
  const sectoralDistributionData = useMemo(() => {
    if (Object.keys(allCategoriesData).length === 0) {
      return [
        { name: 'Sanayi', value: 35 },
        { name: 'Mesken', value: 30 },
        { name: 'Ticarethane', value: 20 },
        { name: 'Aydınlatma', value: 10 },
        { name: 'Diğer', value: 5 },
      ]
    }

    // Kategori bazında dağılım (şimdilik eşit dağıtıyoruz, gerçek veri için API'den çekilebilir)
    // NOT: Burası normalde allCategoriesData'dan hesaplanmalı
    return [
      { name: 'Sanayi', value: 35 },
      { name: 'Mesken', value: 30 },
      { name: 'Ticarethane', value: 20 },
      { name: 'Aydınlatma', value: 10 },
      { name: 'Diğer', value: 5 },
    ]
  }, [allCategoriesData])

  // 4. SEKTÖREL ANOMALİ SAYILARI PASTA (Küçük) - TÜM kategorilerden
  const sectoralAnomalyData = useMemo(() => {
    if (Object.keys(allCategoriesData).length === 0) {
      return [
        { name: 'Sanayi', value: 3 },
        { name: 'Mesken', value: 2 },
        { name: 'Ticarethane', value: 1 },
      ]
    }

    // Her kategorideki anomali sayısını hesapla
    const categoryNames: Record<string, string> = {
      'sanayi': 'Sanayi',
      'mesken': 'Mesken',
      'ticarethane': 'Ticarethane',
      'aydinlatma': 'Aydınlatma',
      'tarimsal': 'Tarımsal',
      'diger': 'Diğer'
    }

    return Object.entries(allCategoriesData)
      .filter(([key]) => key !== 'genel')
      .map(([key, data]) => ({
        name: categoryNames[key] || key,
        value: data.filter(d => d.anomali).length
      }))
      .filter(item => item.value > 0) // Anomalisi olmayanları çıkar
  }, [allCategoriesData])

  const CATEGORY_COLORS: Record<string, string> = {
    'Sanayi': '#fbbf24',    // Sarı/Turuncu
    'Mesken': '#a78bfa',    // Mor
    'Ticarethane': '#c084fc', // Açık Mor
    'Aydınlatma': '#fcd34d',  // Açık Sarı
    'Tarımsal': '#e879f9',   // Fuchsia (Mor uyumlu)
    'Diğer': '#818cf8',      // Indigo (Mor uyumlu)
    'default': '#d8b4fe'
  }

  // Pastel renkler (Gündüz modu için)
  const CATEGORY_COLORS_PASTEL: Record<string, string> = {
    'Sanayi': '#fde047',    // Pastel Sarı
    'Mesken': '#c4b5fd',    // Pastel Mor
    'Ticarethane': '#e9d5ff', // Çok açık Mor
    'Aydınlatma': '#fef3c7',  // Krem Sarı
    'Tarımsal': '#f5d0fe',   // Pastel Pembe/Mor
    'Diğer': '#c7d2fe',      // Pastel Mavi/Indigo
    'default': '#ddd6fe'
  }
  const currentCategoryColors = dark ? CATEGORY_COLORS : CATEGORY_COLORS_PASTEL

  const ANOMALY_COLOR = dark ? '#ef4444' : '#e879f9' // Kırmızı (Gece) / Pembe (Gündüz)

  return (
    <div className={`min-h-screen transition-colors duration-200 ease-in-out ${dark ? 'bg-[#000035] text-gray-100' : 'bg-[#7aa4f5] text-gray-100'}`}>
      <header className={`fixed top-0 left-0 right-0 z-50 border-b transition-colors duration-200 ease-in-out ${dark ? 'border-white/10 bg-[#000035]/95' : 'border-white/20 bg-[#7aa4f5]/95'}`}>
        <div className="mx-auto w-full px-6 py-5 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4 flex-shrink-0">
            {/* Theme Toggle - Top Left as requested */}

            <img
              src="/lightning (4).png"
              alt="ElektrAize Logo"
              className="h-16 w-auto object-contain"
            />
            <div>
              <h1 className="text-5xl font-semibold tracking-tight text-white">ElektrAize</h1>
            </div>
          </div>
          <div className="flex items-center gap-5 flex-wrap justify-end">
            {/* Animated Filter Buttons */}
            <div className="flex items-center gap-4 relative">
              {filterCategories.map((category, index) => {
                // Her butonun yaklaşık genişliği + gap = ~70px (yuvarlak butonlar için)
                const buttonWidth = 70
                const startOffset = buttonWidth * (index + 1)
                return (
                  <div key={category.label} className="relative group">
                    <button
                      onClick={() => setSelectedFilter(category.label)}
                      className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/30 transition-all duration-200"
                      style={{
                        transform: filterOpen
                          ? `translateX(0)`
                          : `translateX(${startOffset}px)`,
                        opacity: filterOpen ? 1 : 0,
                        pointerEvents: filterOpen ? 'auto' : 'none',
                        transition: filterOpen
                          ? `transform 0.5s cubic - bezier(0.34, 1.56, 0.64, 1), opacity 0.4s ease - out`
                          : `transform 0.35s cubic - bezier(0.55, 0.055, 0.675, 0.19), opacity 0.2s ease -in `,
                        transitionDelay: filterOpen
                          ? `${index * 0.05} s`
                          : `${(filterCategories.length - index - 1) * 0.03} s`,
                      }}
                    >
                      <img
                        src={category.icon}
                        alt={category.label}
                        className="w-12 h-12 object-contain"
                      />
                    </button>
                    {/* Tooltip - sadece filtrele açıkken görünsün */}
                    {filterOpen && (
                      <div className="absolute right-0 -top-1 translate-x-full mr-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                        <div className={`border rounded-md px-2 py-1 text-xs shadow-lg ${dark ? 'bg-[#000035]/95 border-white/20 text-gray-200' : 'bg-[#e0e7ff] border-white/50 text-[#000035] font-medium'}`}>
                          {category.displayName}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            <div className="relative">
              <button
                onClick={() => setFilterOpen(!filterOpen)}
                className="inline-flex items-center gap-2 rounded-md border border-white/20 px-4 py-2.5 text-base shadow-sm bg-white/10 hover:bg-white/30 transition whitespace-nowrap"
              >
                <span>Filtrele</span>
              </button>
              {/* Tik işareti - filtre seçildiğinde */}
              {selectedFilter && (
                <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center border-2 border-[#000035]">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
            </div>
            <div className="relative date-picker-container">
              <button
                onClick={() => setDatePickerOpen(!datePickerOpen)}
                className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/30 transition-all duration-200 relative"
                title="Tarih aralığı seç"
              >
                <img
                  src="/calendar (1).png"
                  alt="Tarih seçici"
                  className="w-12 h-12 object-contain"
                />
                {/* Tik işareti - tarih seçildiğinde */}
                {startDate && endDate && (
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center border-2 border-[#000035]">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )}
              </button>
              {datePickerOpen && (
                <div className={`absolute right-0 top-12 z-50 border rounded-lg p-5 shadow-2xl min-w-[340px] animate-in fade-in zoom-in duration-200 ${dark ? 'bg-[#000035] border-white/20' : 'bg-[#7aa4f5] border-white/30'}`}>
                  <div className="flex flex-col gap-4">
                    <DateSelector
                      label="Başlangıç Tarihi"
                      value={tempStartDate || startDate}
                      onChange={setTempStartDate}
                      dark={dark}
                    />
                    <DateSelector
                      label="Bitiş Tarihi"
                      value={tempEndDate || endDate}
                      onChange={setTempEndDate}
                      dark={dark}
                    />

                    <div className="flex gap-2 justify-end mt-2 pt-2 border-t border-white/10">
                      <button
                        onClick={() => {
                          setStartDate('')
                          setEndDate('')
                          setTempStartDate('')
                          setTempEndDate('')
                          setDatePickerOpen(false)
                        }}
                        className={`px-4 py-2 text-sm rounded-md transition border ${dark ? 'bg-white/5 hover:bg-white/10 border-white/20 text-gray-300' : 'bg-white/20 hover:bg-white/40 border-white/30 text-white'}`}
                      >
                        Temizle
                      </button>
                      <button
                        onClick={() => {
                          if (tempStartDate) setStartDate(tempStartDate)
                          if (tempEndDate) setEndDate(tempEndDate)
                          setDatePickerOpen(false)
                        }}
                        className="px-4 py-2 text-sm rounded-md bg-cyan-600 hover:bg-cyan-500 transition text-white font-medium shadow-lg shadow-cyan-500/20"
                      >
                        Tamam
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Contact Form Button */}
            <div className="relative">
              <button
                onClick={() => setContactFormOpen(!contactFormOpen)}
                className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/30 transition-all duration-200"
                title="Bize Ulaşın"
              >
                <img
                  src="/communication.png"
                  alt="İletişim"
                  className="w-12 h-12 object-contain"
                />
              </button>
              {contactFormOpen && (
                <div className={`absolute right-0 top-12 z-50 border rounded-lg p-5 shadow-2xl min-w-[400px] animate-in fade-in zoom-in duration-200 ${dark ? 'bg-[#000035] border-white/20' : 'bg-[#7aa4f5] border-white/30'}`}>
                  <div className="flex flex-col gap-2">
                    {/* Biz.png Icon - Larger */}
                    <div className="flex justify-center">
                      <img
                        src="/biz(1).png"
                        alt="Bize Ulaşın"
                        className="h-40 w-auto object-contain"
                      />
                    </div>

                    <h3 className="text-lg font-semibold text-center text-white mb-2">Bize Ulaşın</h3>

                    {/* Subject Field */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-1">Konu</label>
                      <input
                        type="text"
                        value={contactSubject}
                        onChange={(e) => setContactSubject(e.target.value)}
                        placeholder="Mesaj konusu..."
                        className={`w-full px-4 py-2 rounded-md border ${dark ? 'bg-white/5 border-white/10 text-white' : 'bg-white/10 border-white/20 text-white'} placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50`}
                      />
                    </div>

                    {/* Email Field */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-1">E-posta</label>
                      <input
                        type="email"
                        value={contactEmail}
                        onChange={(e) => setContactEmail(e.target.value)}
                        placeholder="ornek@email.com"
                        className={`w-full px-4 py-2 rounded-md border ${dark ? 'bg-white/5 border-white/10 text-white' : 'bg-white/10 border-white/20 text-white'} placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50`}
                      />
                    </div>

                    {/* Message Field */}
                    <div>
                      <label className="block text-sm font-medium text-white/90 mb-1">Mesaj</label>
                      <textarea
                        value={contactMessage}
                        onChange={(e) => setContactMessage(e.target.value)}
                        placeholder="Mesajınızı buraya yazın..."
                        rows={4}
                        className={`w-full px-4 py-2 rounded-md border resize-none ${dark ? 'bg-white/5 border-white/10 text-white' : 'bg-white/10 border-white/20 text-white'} placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500/50`}
                      />
                    </div>

                    <div className="flex gap-2 justify-end mt-2 pt-2 border-t border-white/10">
                      <button
                        onClick={() => {
                          setContactSubject('')
                          setContactMessage('')
                          setContactFormOpen(false)
                        }}
                        className={`px-4 py-2 text-sm rounded-md transition border ${dark ? 'bg-white/5 hover:bg-white/10 border-white/20 text-gray-300' : 'bg-white/20 hover:bg-white/40 border-white/30 text-white'}`}
                      >
                        İptal
                      </button>
                      <button
                        onClick={async () => {
                          if (!contactSubject || !contactEmail || !contactMessage) {
                            alert('Lütfen tüm alanları doldurun!')
                            return
                          }

                          setContactSending(true)
                          try {
                            // Send email via backend Resend API
                            const params = new URLSearchParams({
                              subject: contactSubject,
                              from_email: contactEmail,
                              message: contactMessage
                            })

                            const response = await fetch(`http://localhost:8000/send-contact-email?${params}`, {
                              method: 'POST'
                            })

                            if (response.ok) {
                              alert('Mesajınız başarıyla gönderildi!')
                              setContactSubject('')
                              setContactMessage('')
                              setContactFormOpen(false)
                            } else {
                              alert('Mesaj gönderilemedi. Lütfen tekrar deneyin.')
                            }
                          } catch (error) {
                            console.error('Email send error:', error)
                            alert('Bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
                          } finally {
                            setContactSending(false)
                          }
                        }}
                        disabled={contactSending}
                        className="px-4 py-2 text-sm rounded-md bg-purple-600 hover:bg-purple-500 transition text-white font-medium shadow-lg shadow-purple-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {contactSending ? 'Gönderiliyor...' : 'Gönder'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Theme Toggle - Moved to Far Right */}
            <button
              onClick={() => setDark((v) => !v)}
              className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/30 dark:hover:bg-white/10 transition-all duration-200 ml-2"
              title={dark ? 'Gündüz moduna geç' : 'Gece moduna geç'}
            >
              <img
                src={dark ? '/crescent-moon.png' : '/contrast.png'}
                alt={dark ? 'Gece modu' : 'Gündüz modu'}
                className="w-12 h-12 object-contain filter drop-shadow-md"
              />
            </button >
          </div >
        </div >
      </header >

      <main className="pt-2">
        {/* Türkiye Haritası */}
        <section className={`relative z-10 w-full ${!dark ? 'light-mode-tooltip' : ''}`}>
          <div className="mx-auto w-full px-4">
            <div className="flex items-center justify-center w-full">
              <div className="w-full max-w-6xl">
                <TurkeyMap onCitySelect={setSelectedCity} dark={dark} />
              </div>
            </div>
          </div>
        </section>

        {/* Grafikler Bölümü */}
        <section ref={chartsSectionRef} className="py-16">
          <div className="w-full">
            <div className="flex items-center justify-center gap-3 mb-1">
              {loading && <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>}
              <h2 className="text-2xl font-bold text-center">
                Enerji İstatistikleri
                {!selectedCity && <span className="ml-3 text-lg font-normal text-[#d8b4fe]/70">(Lütfen şehir seçiniz)</span>}
              </h2>
            </div>

            {/* Ranking Message Moved to Charts Section */}

            {/* Error State */}
            {error && !loading && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-6 mb-8">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-semibold text-red-400">Veri Yükleme Hatası</h3>
                    <p className="text-sm text-red-300 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Info Message */}
            {/* Info Message Removed */}

            {/* Success Message Removed */}

            {/* DOĞRU LAYOUT */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8 px-2 ml-8">
              {/* SOL: Aylık Tüketim - 1/2 genişlik */}
              <div className={`rounded-2xl p-4 pb-0 border relative transition-all duration-200 ease-in-out ${dark ? 'bg-[#a78bfa]/30 border-white/10' : 'bg-white/30 border-blue-200 shadow-sm'}`}>
                {/* SEKTÖR İKONU - SAĞ ÜST KÖŞE */}
                {(() => {
                  const currentCategory = filterCategories.find(c => c.label === (selectedFilter || 'genel'))
                  if (currentCategory) {
                    return (
                      <div className={`absolute top-4 right-4 p-2 rounded-lg border shadow-xl ${dark ? 'bg-[#000035]/50 border-white/10' : 'bg-white/30 border-blue-200'}`} title={`Seçili Sektör: ${currentCategory.displayName}`}>
                        <img
                          src={currentCategory.icon}
                          alt={currentCategory.displayName}
                          className="w-8 h-8 object-contain"
                        />
                      </div>
                    )
                  }
                  return null
                })()}

                <h3 className="text-lg font-semibold mb-3">Aylık Tüketim Analizi (MWh)</h3>
                <ResponsiveContainer width="100%" height={380}>
                  <LineChart data={monthlyMainData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={dark ? "rgba(199, 151, 255, 0.3)" : "rgba(59, 130, 246, 0.3)"} />
                    <XAxis
                      dataKey="ay"
                      stroke={dark ? "#a78bfa" : "#1d4ed8"}
                      fontSize={10}
                      interval={0}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis stroke={dark ? "#a78bfa" : "#1d4ed8"} fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: dark ? '#000035' : '#e0e7ff', // Light Blue in Day
                        border: dark ? '1px solid #a78bfa' : '1px solid #c7d2fe',
                        borderRadius: '8px',
                        color: dark ? '#fff' : '#000035'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Line
                      type="monotone"
                      dataKey="tahmin"
                      stroke={dark ? "#a78bfa" : "#c4b5fd"}
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Tahmin"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="gerçek"
                      stroke={dark ? "#fbbf24" : "#facc15"} // Saf Sarı (Gündüz)
                      strokeWidth={3}
                      name="Gerçek"
                      dot={(props: any) => {
                        const { cx, cy, payload } = props
                        const isHighDeviation = payload.yüksekFark
                        return (
                          <circle
                            key={`${payload.donem} -${cx} -${cy} `}
                            cx={cx}
                            cy={cy}
                            r={isHighDeviation ? 6 : 4}
                            fill={isHighDeviation ? ANOMALY_COLOR : (dark ? '#fbbf24' : '#facc15')}
                            stroke={isHighDeviation ? '#fff' : 'none'}
                            strokeWidth={isHighDeviation ? 2 : 0}
                          />
                        )
                      }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <div className="mt-2 text-xs text-gray-400 flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <span>Yüksek sapma (%15+)</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-4">
                {/* Günlük Tüketim ve Ranking Row */}
                <div className="flex gap-4">
                  {/* Günlük Tüketim - %40 Genişlik */}
                  <div className={`w-[40%] rounded-xl p-2 border transition-all duration-200 ease-in-out ${dark ? 'bg-[#a78bfa]/30 border-white/10' : 'bg-white/30 border-blue-200 shadow-sm'}`}>
                    <h3 className="text-xs font-semibold mb-1">Günlük Ort. Tüketim (MWh)</h3>
                    <ResponsiveContainer width="100%" height={80}>
                      <AreaChart data={dailyConsumptionData}>
                        <CartesianGrid strokeDasharray="3 3" stroke={dark ? "rgba(255,255,255,0.1)" : "rgba(59, 130, 246, 0.3)"} />
                        <XAxis dataKey="saat" stroke={dark ? "#a78bfa" : "#1d4ed8"} fontSize={7} hide />
                        <YAxis stroke={dark ? "#a78bfa" : "#1d4ed8"} fontSize={7} hide />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: dark ? '#000035' : '#e0e7ff', // Light Blue in Day
                            border: '1px solid #a78bfa',
                            borderRadius: '8px',
                            color: dark ? '#fff' : '#000035',
                            fontSize: '10px'
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="tüketim"
                          stroke={dark ? "#fbbf24" : "#f59e0b"}
                          fill={dark ? "#fbbf24" : "#fcd34d"}
                          fillOpacity={0.6}
                          name="Saatlik Ort."
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Ranking Card - %60 Genişlik */}
                  {/* Ranking Card - %60 Genişlik */}
                  <div className={`flex-1 rounded-xl p-4 border flex items-center justify-center text-center transition-all duration-200 ease-in-out ${dark ? 'bg-[#a78bfa]/30 border-white/10 shadow-lg' : 'bg-white/30 border-blue-200 shadow-sm'}`}>
                    {rankingData && selectedCity ? (
                      <p className="text-sm text-gray-100 leading-relaxed font-light">
                        <span className={`font-bold text-base block mb-1 ${dark ? 'text-[#f5d0fe]' : 'text-[#e879f9]'}`}>{selectedCity.name}</span>
                        Türkiye'de <span className={`font-bold ${dark ? 'text-white' : 'text-blue-700'}`}>{filterCategories.find(c => c.label === (selectedFilter || 'genel'))?.displayName || 'Genel'}</span> sektöründe <span className="font-bold text-[#fbbf24] text-lg">{rankingData.rank}.</span> sırada.
                        <span className="block text-xs text-gray-400 mt-1">({rankingData.anomaly_count} anomali)</span>
                      </p>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-gray-400 text-xs">
                        <span className="mb-1 text-xl">🏆</span>
                        <p>Sıralama için şehir seçiniz</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Pastalar: Anomali sol üstte küçük, Sektörel sağda KOCAMAN */}
                <div className="relative" style={{ height: '460px' }}>
                  {!selectedCity || !selectedFilter || !startDate || !endDate ? (
                    <>
                      {/* Anomali Sayıları Placeholder */}
                      <div className="absolute left-0 top-0 z-10 flex flex-col items-center gap-6" style={{ width: '40%' }}>
                        <h3 className="text-sm font-semibold text-center mt-2">Anomali Sayıları</h3>
                        <div className={`relative rounded-full border border-white/10 shadow-xl flex-shrink-0 flex items-center justify-center ${dark ? 'bg-[#a78bfa]/30' : 'bg-white/30'}`} style={{ width: '260px', height: '260px' }}>
                          <svg viewBox="0 0 220 220" className="w-[220px] h-[220px]">
                            <circle cx="110" cy="110" r="110" fill={dark ? "#fbbf24" : "#fde047"} />
                            {/* Gözler: Biraz yukarıda, aralıklı */}
                            <circle cx="75" cy="90" r="12" fill="white" />
                            <circle cx="145" cy="90" r="12" fill="white" />
                            {/* Ağız: Yarım daire benzeri çizgi, aşağıda */}
                            <path d="M 70 140 Q 110 180 150 140" stroke="white" strokeWidth="8" fill="none" strokeLinecap="round" />
                          </svg>
                        </div>
                      </div>

                      {/* Sektörel Dağılım Placeholder */}
                      <div className="absolute right-0 top-0 flex flex-col items-center gap-6" style={{ width: '420px', height: '100%' }}>
                        <h3 className="text-sm font-semibold text-center mt-2">Sektörel Dağılım</h3>
                        <div className={`relative rounded-full border border-white/10 shadow-xl flex-shrink-0 flex items-center justify-center ${dark ? 'bg-[#a78bfa]/30' : 'bg-white/30'}`} style={{ width: '380px', height: '380px' }}>
                          <svg viewBox="0 0 340 340" className="w-[340px] h-[340px]">
                            <circle cx="170" cy="170" r="170" fill={dark ? "#fbbf24" : "#fde047"} />
                            {/* Gözler: Biraz yukarıda, aralıklı */}
                            <circle cx="115" cy="140" r="18" fill="white" />
                            <circle cx="225" cy="140" r="18" fill="white" />
                            {/* Ağız: Yarım daire benzeri çizgi, aşağıda */}
                            <path d="M 110 220 Q 170 280 230 220" stroke="white" strokeWidth="12" fill="none" strokeLinecap="round" />
                          </svg>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* Anomali Sayıları - Sol üstte (Outline Görünüm) */}
                      <div className="absolute left-0 top-0 z-10 flex flex-col items-center gap-6" style={{ width: '40%' }}>
                        <h3 className="text-sm font-semibold text-center mt-2">Anomali Sayıları</h3>
                        <div className={`relative rounded-full border border-white/10 shadow-xl flex-shrink-0 flex items-center justify-center ${dark ? 'bg-[#a78bfa]/30' : 'bg-white/30'}`} style={{ width: '260px', height: '260px' }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={sectoralAnomalyData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ cx, cy, midAngle, outerRadius, value }: any) => {
                                  if (value === 0) return null
                                  const RADIAN = Math.PI / 180
                                  const radius = 25 + (outerRadius - 25) * 0.5 // 25 innerRadius varsayımıyla (aslında 0)
                                  const x = cx + radius * Math.cos(-midAngle * RADIAN)
                                  const y = cy + radius * Math.sin(-midAngle * RADIAN)

                                  return (
                                    <text
                                      x={x}
                                      y={y}
                                      fill="white"
                                      textAnchor="middle"
                                      dominantBaseline="central"
                                      className="text-xs font-bold"
                                    >
                                      {value}
                                    </text>
                                  )
                                }}
                                isAnimationActive={false}
                                outerRadius={110}
                                dataKey="value"
                              >
                                {sectoralAnomalyData.map((entry: any, index: number) => (
                                  <Cell
                                    key={`cell - ${index} `}
                                    fill={currentCategoryColors[entry.name] || currentCategoryColors['default']}
                                  />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: dark ? '#3a49b8' : '#e0e7ff', // Light Blue in Day
                                  border: '1px solid #a78bfa',
                                  borderRadius: '8px',
                                  color: dark ? '#fff' : '#000035'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        {/* Legend altında - TÜM kategoriler (Daire ve Biraz Büyük Font) */}
                        <div className="grid grid-cols-2 grid-rows-3 grid-flow-col gap-x-4 gap-y-2 text-sm mt-3 w-full pl-10">
                          {['Sanayi', 'Mesken', 'Ticarethane', 'Aydınlatma', 'Tarımsal', 'Diğer'].map((name, index) => (
                            <div key={index} className="flex items-center gap-2">
                              <div
                                className="w-4 h-4 rounded-full flex-shrink-0"
                                style={{ backgroundColor: currentCategoryColors[name] || currentCategoryColors['default'] }}
                              ></div>
                              <span className={`text-sm font-light ${dark ? 'text-gray-200' : 'text-gray-800'}`}>{name}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Sektörel Dağılım - Sağda KOCAMAN ve Yuvarlak (Outline Görünüm) */}
                      <div className="absolute right-0 top-0 flex flex-col items-center gap-6" style={{ width: '420px', height: '100%' }}>
                        <h3 className="text-sm font-semibold text-center mt-2">Sektörel Dağılım</h3>
                        <div className={`relative rounded-full border border-white/10 shadow-xl flex-shrink-0 flex items-center justify-center ${dark ? 'bg-[#a78bfa]/30' : 'bg-white/30'}`} style={{ width: '380px', height: '380px' }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={sectoralDistributionData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
                                  const RADIAN = Math.PI / 180
                                  const radius = innerRadius + (outerRadius - innerRadius) * 0.5
                                  const x = cx + radius * Math.cos(-midAngle * RADIAN)
                                  const y = cy + radius * Math.sin(-midAngle * RADIAN)

                                  return (
                                    <text
                                      x={x}
                                      y={y}
                                      fill="white"
                                      textAnchor="middle"
                                      dominantBaseline="central"
                                      className="text-sm font-bold"
                                    >
                                      {`${(percent * 100).toFixed(0)}% `}
                                    </text>
                                  )
                                }}
                                isAnimationActive={false}
                                outerRadius={170}
                                dataKey="value"
                              >
                                {sectoralDistributionData.map((entry: any, index: number) => (
                                  <Cell key={`cell - ${index} `} fill={currentCategoryColors[entry.name] || currentCategoryColors['default']} />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: dark ? '#3a49b8' : '#e0e7ff', // Light Blue in Day
                                  border: '1px solid #a78bfa',
                                  borderRadius: '8px',
                                  color: dark ? '#fff' : '#000035'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                      {/* Fixed syntax */}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Alt bilgi kaldırıldı */}
    </div >
  )
}


