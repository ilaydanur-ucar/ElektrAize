import { useEffect, useMemo, useState, useRef } from 'react'
import LeafletTurkeyMap from './components/LeafletTurkeyMap'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts'

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

interface AnomalyData {
  sehir: string
  donem: string
  gercek: number
  tahmin: number
  residual: number
  anomali: boolean
  baseline?: number
  dev_pct?: number
  alt_limit?: number
  ust_limit?: number
  category?: string
}

// Frontend kategori isimleri -> Backend kategori isimleri mapping
const categoryMapping: Record<string, string> = {
  'aydınlanma': 'aydinlatma',
  'mesken': 'mesken',
  'ticaret': 'ticarethane',
  'sanayi': 'sanayi',
  'tarım': 'tarimsal',
  'genel': 'genel',
  'diğer': 'diger',
}

function App() {
  const [dark, setDark] = useState(false)
  const [datePickerOpen, setDatePickerOpen] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [filterOpen, setFilterOpen] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [chartData, setChartData] = useState<any>(null)
  const chartsSectionRef = useRef<HTMLElement>(null)

  const scrollToCharts = () => {
    chartsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const filterCategories = [
    { label: 'aydınlanma', icon: '/light-bulb.png' },
    { label: 'mesken', icon: '/house.png' },
    { label: 'ticaret', icon: '/dollar.png' },
    { label: 'sanayi', icon: '/factory.png' },
    { label: 'tarım', icon: '/wheat.png' },
    { label: 'genel', icon: '/all.png' },
    { label: 'diğer', icon: '/ellipsis.png' },
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

  // Backend'den veri çek
  const fetchChartData = async (category: string, start: string, end: string) => {
    setLoading(true)
    try {
      const backendCategory = categoryMapping[category] || category
      const params = new URLSearchParams()
      params.set('category', backendCategory)
      if (start) params.set('start', start)
      if (end) params.set('end', end)

      const response = await fetch(`${API_URL}/anomalies?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`)
      }

      const data: AnomalyData[] = await response.json()
      
      // Veriyi grafik formatına dönüştür
      const monthlyData = data.reduce((acc: any, item: AnomalyData) => {
        const date = new Date(item.donem)
        const month = date.toLocaleDateString('tr-TR', { month: 'long' })
        const monthKey = month.charAt(0).toUpperCase() + month.slice(1)
        
        if (!acc[monthKey]) {
          acc[monthKey] = { tüketim: 0, üretim: 0, count: 0 }
        }
        acc[monthKey].tüketim += item.gercek
        acc[monthKey].üretim += item.tahmin
        acc[monthKey].count += 1
        
        return acc
      }, {})

      const barData = Object.entries(monthlyData).map(([name, values]: [string, any]) => ({
        name,
        tüketim: Math.round(values.tüketim / values.count) || 0,
      }))

      const lineData = Object.entries(monthlyData).map(([ay, values]: [string, any]) => ({
        ay,
        üretim: Math.round(values.üretim / values.count) || 0,
      }))

      setChartData({ barData, lineData, pieData: [], areaData: [] })
    } catch (error) {
      console.error('Error fetching chart data:', error)
      // Hata durumunda varsayılan verileri kullan
      setChartData(null)
    } finally {
      setLoading(false)
    }
  }

  // Üç koşul da sağlandığında veri çek ve grafiklere scroll yap
  useEffect(() => {
    if (startDate && endDate && selectedFilter) {
      fetchChartData(selectedFilter, startDate, endDate)
      setTimeout(() => {
        scrollToCharts()
      }, 300)
    }
  }, [startDate, endDate, selectedFilter])

  // Grafik verileri - backend'den gelen veri varsa onu kullan, yoksa varsayılan
  const barData = useMemo(() => {
    if (chartData?.barData) return chartData.barData
    return [
      { name: 'Ocak', tüketim: Math.floor(Math.random() * 5000) + 2000 },
      { name: 'Şubat', tüketim: Math.floor(Math.random() * 5000) + 2000 },
      { name: 'Mart', tüketim: Math.floor(Math.random() * 5000) + 2000 },
      { name: 'Nisan', tüketim: Math.floor(Math.random() * 5000) + 2000 },
      { name: 'Mayıs', tüketim: Math.floor(Math.random() * 5000) + 2000 },
      { name: 'Haziran', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    ]
  }, [chartData])

  const lineData = useMemo(() => {
    if (chartData?.lineData) return chartData.lineData
    return [
      { ay: 'Ocak', üretim: Math.floor(Math.random() * 4000) + 3000 },
      { ay: 'Şubat', üretim: Math.floor(Math.random() * 4000) + 3000 },
      { ay: 'Mart', üretim: Math.floor(Math.random() * 4000) + 3000 },
      { ay: 'Nisan', üretim: Math.floor(Math.random() * 4000) + 3000 },
      { ay: 'Mayıs', üretim: Math.floor(Math.random() * 4000) + 3000 },
      { ay: 'Haziran', üretim: Math.floor(Math.random() * 4000) + 3000 },
    ]
  }, [chartData])

  const pieData = useMemo(() => [
    { name: 'Sanayi', value: Math.floor(Math.random() * 300) + 100 },
    { name: 'Konut', value: Math.floor(Math.random() * 300) + 100 },
    { name: 'Ticaret', value: Math.floor(Math.random() * 300) + 100 },
    { name: 'Tarım', value: Math.floor(Math.random() * 300) + 100 },
  ], [])

  const areaData = useMemo(() => [
    { zaman: '00:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '04:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '08:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '12:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '16:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '20:00', güç: Math.floor(Math.random() * 200) + 50 },
  ], [])

  const COLORS = ['#00FFFF', '#3065AC', '#2563EB', '#3b82f6', '#60a5fa']

  return (
    <div className="bg-[#000035] text-gray-100">
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b border-white/10 bg-[#000035]/95">
        <div className="mx-auto w-full px-6 py-5 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4 flex-shrink-0">
            <img 
              src="/Ekran görüntüsü 2025-10-31 200345.png" 
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
                      onClick={() => {
                        setSelectedFilter(category.label)
                      }}
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
                        <div className="bg-[#000035]/95 border border-white/20 rounded-md px-2 py-1 text-xs text-gray-200 capitalize shadow-lg">
                          {category.label}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            <button
              onClick={() => setFilterOpen(!filterOpen)}
              className="inline-flex items-center gap-2 rounded-md border border-white/20 px-4 py-2.5 text-base shadow-sm bg-white/10 hover:bg-white/15 transition whitespace-nowrap"
            >
              <span>Filtrele</span>
            </button>
            <div className="relative date-picker-container">
              <button
                onClick={() => setDatePickerOpen(!datePickerOpen)}
                className="inline-flex items-center justify-center rounded-full w-14 h-14 bg-transparent hover:bg-white/10 transition-all duration-200"
                title="Tarih aralığı seç"
              >
                <img 
                  src="/clock.png" 
                  alt="Tarih seçici"
                  className="w-12 h-12 object-contain"
                />
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

      <main className="pt-24">
        {/* Sadece harita kalsın */}

        <section className="relative z-10">
          <div className="mx-auto max-w-6xl px-4 py-10">
            <div className="flex items-start gap-4">
              {/* Leaflet Map */}
              <div className="relative z-10">
                <LeafletTurkeyMap dark={dark} />
              </div>
            </div>
          </div>
        </section>

        {/* Grafikler Bölümü */}
        <section ref={chartsSectionRef} className="py-16">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-2xl font-bold mb-8 text-center">Enerji İstatistikleri</h2>
            {loading && (
              <div className="text-center py-4 text-cyan-400">
                Veriler yükleniyor...
              </div>
            )}
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Bar Chart */}
              <div className="bg-[#2E3B49]/90 rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4">Aylık Tüketim</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="name" stroke="#93c5fd" />
                    <YAxis stroke="#93c5fd" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e3a8a', border: '1px solid #3065AC', borderRadius: '8px', color: '#fff' }} />
                    <Legend />
                    <Bar dataKey="tüketim" fill="#00FFFF" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Line Chart */}
              <div className="bg-[#2E3B49]/90 rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4">Aylık Üretim</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={lineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="ay" stroke="#93c5fd" />
                    <YAxis stroke="#93c5fd" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e3a8a', border: '1px solid #3065AC', borderRadius: '8px', color: '#fff' }} />
                    <Legend />
                    <Line type="monotone" dataKey="üretim" stroke="#3065AC" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Pie Chart */}
              <div className="bg-[#2E3B49]/90 rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4">Sektör Dağılımı</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(props: any) => {
                        const percent = props.percent as number
                        const name = props.name as string
                        return `${name} ${(percent * 100).toFixed(0)}%`
                      }}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1e3a8a', border: '1px solid #3065AC', borderRadius: '8px', color: '#fff' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Area Chart */}
              <div className="bg-[#2E3B49]/90 rounded-2xl p-6 border border-white/10">
                <h3 className="text-lg font-semibold mb-4">Günlük Güç Dağılımı</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={areaData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="zaman" stroke="#93c5fd" />
                    <YAxis stroke="#93c5fd" />
                    <Tooltip contentStyle={{ backgroundColor: '#1e3a8a', border: '1px solid #3065AC', borderRadius: '8px', color: '#fff' }} />
                    <Legend />
                    <Area type="monotone" dataKey="güç" stroke="#00FFFF" fill="#00FFFF" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
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
