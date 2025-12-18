import { useEffect, useMemo, useState, useRef, useCallback } from 'react'
import TurkeyMap from './components/TurkeyMap'
import { LineChart, Line, PieChart, Pie, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts'
import { fetchAnomalies, type AnomalyItem } from './utils/api'
import { getCityNameFromCode } from './utils/cityMapping'

type FilterCategory = {
  label: string
  displayName: string
  icon: string
}

function App() {
  const [dark, setDark] = useState(false)
  const [datePickerOpen, setDatePickerOpen] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [filterOpen, setFilterOpen] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [selectedCity, setSelectedCity] = useState<{ id: string, name: string } | null>(null)
  const [anomalyData, setAnomalyData] = useState<AnomalyItem[]>([])
  const [allCategoriesData, setAllCategoriesData] = useState<Record<string, AnomalyItem[]>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const chartsSectionRef = useRef<HTMLElement>(null)

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
      console.log(`%c[SÜREÇ] Tüm Kategori Verileri İstendi (${cityName})`, 'color: orange;')
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
            console.warn(`⚠️ ${category} kategorisi yüklenemedi:`, err)
            allData[category] = []
          }
        })
      )

      setAllCategoriesData(allData)
      console.log(`%c[SÜREÇ] Tüm Kategoriler Çekildi:`, 'color: orange;', Object.keys(allData).join(', '))
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
      setError(`Şehir kodu bulunamadı: ${selectedCity.id}`)
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
      setAnomalyData(data)

      // TÜM kategoriler için de veri çek (pasta grafikler için)
      fetchAllCategoriesData(cityName, startDate, endDate)

      // Grafiklere scroll yap
      setTimeout(() => {
        chartsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bilinmeyen hata'
      console.error('❌ API hatası:', errorMessage)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }, [selectedCity, selectedFilter, startDate, endDate, fetchAllCategoriesData])

  // Şehir, filtre veya tarih değiştiğinde veri çek
  useEffect(() => {
    if (selectedCity) {
      fetchCityData()
    }
  }, [selectedCity, selectedFilter, startDate, endDate, fetchCityData])

  // 1. ANA GRAFİK: Aylık Tüketim (Gerçek vs Tahmin) - Fark fazlaysa kırmızı nokta
  const monthlyMainData = useMemo(() => {
    if (anomalyData.length === 0) return []

    // Gelen verideki mevcut tarihleri (Ay Yıl) topla
    const monthlyGroups: Record<string, { tahmin: number[], gercek: number[], dateObj: Date }> = {}

    anomalyData.forEach((item) => {
      const date = new Date(item.donem)
      // Key olarak "YYYY-MM" kullanalım ki sıralama kolay olsun
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`

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

        // Gösterim adı (Örn: Oca 2023)
        const displayMonth = data.dateObj.toLocaleDateString('tr-TR', { month: 'short', year: 'numeric' })

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
    if (anomalyData.length === 0) {
      return [
        { name: 'Sanayi', value: 35 },
        { name: 'Mesken', value: 30 },
        { name: 'Ticarethane', value: 20 },
        { name: 'Aydınlatma', value: 10 },
        { name: 'Diğer', value: 5 },
      ]
    }

    // Kategori bazında dağılım (şimdilik eşit dağıtıyoruz, gerçek veri için API'den çekilebilir)

    return [
      { name: 'Sanayi', value: 35 },
      { name: 'Mesken', value: 30 },
      { name: 'Ticarethane', value: 20 },
      { name: 'Aydınlatma', value: 10 },
      { name: 'Diğer', value: 5 },
    ]
  }, [anomalyData])

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
    'Tarımsal': '#34d399',   // Yeşil
    'Diğer': '#9ca3af',      // Gri
    'default': '#d8b4fe'
  }
  const ANOMALY_COLOR = '#ef4444' // Kırmızı

  return (
    <div className="bg-[#000035] text-gray-100">
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b border-white/10 bg-[#000035]/95">
        <div className="mx-auto w-full px-6 py-5 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4 flex-shrink-0">
            <img
              src="/lightning (1).png"
              alt="ElektrAize Logo"
              className="h-16 w-auto object-contain"
            />
            <div>
              <h1 className="text-5xl font-semibold tracking-tight">ElektrAize</h1>
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
                      className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/10 transition-all duration-200"
                      style={{
                        transform: filterOpen
                          ? `translateX(0)`
                          : `translateX(${startOffset}px)`,
                        opacity: filterOpen ? 1 : 0,
                        pointerEvents: filterOpen ? 'auto' : 'none',
                        transition: filterOpen
                          ? `transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.4s ease-out`
                          : `transform 0.35s cubic-bezier(0.55, 0.055, 0.675, 0.19), opacity 0.2s ease-in`,
                        transitionDelay: filterOpen
                          ? `${index * 0.05}s`
                          : `${(filterCategories.length - index - 1) * 0.03}s`,
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
                        <div className="bg-[#000035]/95 border border-white/20 rounded-md px-2 py-1 text-xs text-gray-200 shadow-lg">
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
                className="inline-flex items-center gap-2 rounded-md border border-white/20 px-4 py-2.5 text-base shadow-sm bg-white/10 hover:bg-white/15 transition whitespace-nowrap"
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
                className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/10 transition-all duration-200 relative"
                title="Tarih aralığı seç"
              >
                <img
                  src="/clock.png"
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
                <div className="absolute right-0 top-12 z-50 bg-[#000035] border border-white/20 rounded-lg p-4 shadow-xl min-w-[280px]">
                  <div className="flex flex-col gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-300">Başlangıç Tarihi</label>
                      <input
                        type="date"
                        min="2020-01-01"
                        max="2025-12-31"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1 text-gray-300">Bitiş Tarihi</label>
                      <input
                        type="date"
                        min="2020-01-01"
                        max="2025-12-31"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 text-sm"
                      />
                    </div>
                    <div className="flex gap-2 justify-end mt-2">
                      <button
                        onClick={() => {
                          setStartDate('')
                          setEndDate('')
                          setDatePickerOpen(false)
                        }}
                        className="px-3 py-1.5 text-sm rounded-md bg-white/10 hover:bg-white/15 transition border border-white/20"
                      >
                        Temizle
                      </button>
                      <button
                        onClick={() => setDatePickerOpen(false)}
                        className="px-3 py-1.5 text-sm rounded-md bg-cyan-500 hover:bg-cyan-600 transition"
                      >
                        Tamam
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={() => setDark((v) => !v)}
              className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/10 transition-all duration-200"
              title={dark ? 'Gündüz moduna geç' : 'Gece moduna geç'}
            >
              <img
                src={dark ? '/crescent-moon.png' : '/contrast.png'}
                alt={dark ? 'Gece modu' : 'Gündüz modu'}
                className="w-12 h-12 object-contain"
              />
            </button>
          </div>
        </div>
      </header>

      <main className="pt-2">
        {/* Türkiye Haritası */}
        <section className="relative z-10 w-full">
          <div className="mx-auto w-full px-4">
            <div className="flex items-center justify-center w-full">
              <div className="w-full max-w-6xl">
                <TurkeyMap onCitySelect={setSelectedCity} />
              </div>
            </div>
          </div>
        </section>

        {/* Grafikler Bölümü */}
        <section ref={chartsSectionRef} className="py-16">
          <div className="w-full">
            <h2 className="text-2xl font-bold mb-8 text-center">Enerji İstatistikleri</h2>

            {/* Loading State */}
            {loading && (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500"></div>
                <p className="mt-4 text-gray-400">Veriler yükleniyor...</p>
              </div>
            )}

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
            {!selectedCity && !loading && (
              <div className="bg-blue-500/10 border border-blue-500/50 rounded-lg p-6 mb-8">
                <div className="flex items-start gap-3">
                  <svg className="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <h3 className="font-semibold text-blue-400">Haritadan Şehir Seçin</h3>
                    <p className="text-sm text-blue-300 mt-1">Gerçek enerji verilerini görmek için yukarıdaki haritadan bir şehir seçin.</p>
                  </div>
                </div>
              </div>
            )}

            {/* Success Message */}
            {selectedCity && anomalyData.length > 0 && !loading && !error && (
              <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4 mb-8">
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm text-green-300">
                    <span className="font-semibold">{selectedCity.name}</span> için <span className="font-semibold">{anomalyData.length}</span> kayıt yüklendi
                  </p>
                </div>
              </div>
            )}

            {/* DOĞRU LAYOUT */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8 px-2 ml-8">
              {/* SOL: Aylık Tüketim - 1/2 genişlik */}
              <div className="bg-[#a78bfa]/30 rounded-2xl p-4 border border-white/10 relative">
                {/* SEKTÖR İKONU - SAĞ ÜST KÖŞE */}
                {(() => {
                  const currentCategory = filterCategories.find(c => c.label === (selectedFilter || 'genel'))
                  if (currentCategory) {
                    return (
                      <div className="absolute top-4 right-4 bg-[#000035]/50 p-2 rounded-lg border border-white/10 backdrop-blur-sm shadow-xl" title={`Seçili Sektör: ${currentCategory.displayName}`}>
                        <img
                          src={currentCategory.icon}
                          alt={currentCategory.displayName}
                          className="w-8 h-8 object-contain filter brightness-100 invert"
                        />
                      </div>
                    )
                  }
                  return null
                })()}

                <h3 className="text-lg font-semibold mb-3">Aylık Tüketim Analizi (MWh)</h3>
                <ResponsiveContainer width="100%" height={450}>
                  <LineChart data={monthlyMainData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(199, 151, 255, 0.3)" />
                    <XAxis dataKey="ay" stroke="#a78bfa" fontSize={11} />
                    <YAxis stroke="#a78bfa" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#000035',
                        border: '1px solid #a78bfa',
                        borderRadius: '8px',
                        color: '#fff'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Line
                      type="monotone"
                      dataKey="tahmin"
                      stroke="#a78bfa"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name="Tahmin"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="gerçek"
                      stroke="#fbbf24"
                      strokeWidth={3}
                      name="Gerçek"
                      dot={(props: any) => {
                        const { cx, cy, payload } = props
                        const isHighDeviation = payload.yüksekFark
                        return (
                          <circle
                            key={`${payload.donem}-${cx}-${cy}`}
                            cx={cx}
                            cy={cy}
                            r={isHighDeviation ? 6 : 4}
                            fill={isHighDeviation ? ANOMALY_COLOR : '#fbbf24'}
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

              {/* SAĞ: Günlük + Pastalar */}
              <div className="flex flex-col gap-4">
                {/* Günlük Tüketim - ÇOK ÇOK KÜÇÜK (kırmızı kutu boyutunda) */}
                <div className="w-2/5 bg-[#a78bfa]/30 rounded-xl p-2 border border-white/10">
                  <h3 className="text-xs font-semibold mb-1">Günlük Ort. Tüketim (MWh)</h3>
                  <ResponsiveContainer width="100%" height={80}>
                    <AreaChart data={dailyConsumptionData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="saat" stroke="#a78bfa" fontSize={7} hide />
                      <YAxis stroke="#a78bfa" fontSize={7} hide />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#000035',
                          border: '1px solid #a78bfa',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '10px'
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="tüketim"
                        stroke="#fbbf24"
                        fill="#fbbf24"
                        fillOpacity={0.6}
                        name="Saatlik Ort."
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Pastalar: Anomali sol üstte küçük, Sektörel sağda KOCAMAN */}
                <div className="relative" style={{ height: '420px' }}>
                  {/* Anomali Sayıları - Sol üstte KÜÇÜK */}
                  <div className="absolute left-0 top-0 z-10" style={{ width: '40%' }}>
                    <h3 className="text-xs font-semibold mb-1">Anomali Sayıları</h3>
                    <ResponsiveContainer width="100%" height={200}>
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
                          outerRadius={60}
                          dataKey="value"
                        >
                          {sectoralAnomalyData.map((entry: any, index: number) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={CATEGORY_COLORS[entry.name] || CATEGORY_COLORS['default']}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#000035',
                            border: '1px solid #a78bfa',
                            borderRadius: '8px',
                            color: '#fff'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                    {/* Legend altında - TÜM kategoriler */}
                    <div className="flex flex-col gap-1 text-xs mt-1">
                      {['Sanayi', 'Mesken', 'Ticarethane', 'Aydınlatma', 'Tarımsal', 'Diğer'].map((name, index) => (
                        <div key={index} className="flex items-center gap-1">
                          <div
                            className="w-3 h-3 rounded-sm flex-shrink-0"
                            style={{ backgroundColor: CATEGORY_COLORS[name] || CATEGORY_COLORS['default'] }}
                          ></div>
                          <span className="text-gray-300 text-xs">{name}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Sektörel Dağılım - Sağda KOCAMAN */}
                  <div className="absolute right-0 top-0" style={{ width: '100%' }}>
                    <h3 className="text-sm font-semibold mb-2">Sektörel Dağılım</h3>
                    <ResponsiveContainer width="100%" height={380}>
                      <PieChart>
                        <Pie
                          data={sectoralDistributionData}
                          cx="60%"
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
                                {`${(percent * 100).toFixed(0)}%`}
                              </text>
                            )
                          }}
                          outerRadius={130}
                          dataKey="value"
                        >
                          {sectoralDistributionData.map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.name] || CATEGORY_COLORS['default']} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#000035',
                            border: '1px solid #a78bfa',
                            borderRadius: '8px',
                            color: '#fff'
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Alt bilgi kaldırıldı */}
    </div>
  )
}

export default App
