import { useEffect, useMemo, useState, useRef } from 'react'
import LeafletTurkeyMap from './components/LeafletTurkeyMap'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts'

function App() {
  const [dark, setDark] = useState(false)
  const [datePickerOpen, setDatePickerOpen] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [filterOpen, setFilterOpen] = useState(false)
  const [selectedFilter, setSelectedFilter] = useState<string | null>(null)
  const [selectedCity, setSelectedCity] = useState<string | null>(null)        
  const chartsSectionRef = useRef<HTMLElement>(null)

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

  // İkisi de seçildiğinde scroll yap ve grafikleri güncelle
  useEffect(() => {
    if (selectedFilter && startDate && endDate) {
      setTimeout(() => {
        chartsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 300)
      // Grafik verilerini rastgele güncellemek için state'i tetikle
      // useMemo bağımlılıklarına selectedFilter, startDate, endDate ekleyerek yeniden hesaplama yapılacak
    }
  }, [selectedFilter, startDate, endDate])

  // Rastgele grafik verileri - filtre ve tarih seçildiğinde yeniden hesaplanır
  const barData = useMemo(() => [
    { name: 'Ocak', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Şubat', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Mart', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Nisan', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Mayıs', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Haziran', tüketim: Math.floor(Math.random() * 5000) + 2000 },
  ], [selectedFilter, startDate, endDate])

  const lineData = useMemo(() => [
    { ay: 'Ocak', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Şubat', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Mart', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Nisan', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Mayıs', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Haziran', üretim: Math.floor(Math.random() * 4000) + 3000 },
  ], [selectedFilter, startDate, endDate])

  const pieData = useMemo(() => [
    { name: 'Sanayi', value: Math.floor(Math.random() * 300) + 100 },
    { name: 'Konut', value: Math.floor(Math.random() * 300) + 100 },
    { name: 'Ticaret', value: Math.floor(Math.random() * 300) + 100 },
    { name: 'Tarım', value: Math.floor(Math.random() * 300) + 100 },
  ], [selectedFilter, startDate, endDate])

  const areaData = useMemo(() => [
    { zaman: '00:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '04:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '08:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '12:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '16:00', güç: Math.floor(Math.random() * 200) + 50 },
    { zaman: '20:00', güç: Math.floor(Math.random() * 200) + 50 },
  ], [selectedFilter, startDate, endDate])

  const COLORS = ['#a78bfa', '#fbbf24', '#c084fc', '#fcd34d', '#d8b4fe']

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
                        <div className="bg-[#000035]/95 border border-white/20 rounded-md px-2 py-1 text-xs text-gray-200 capitalize shadow-lg">
                          {category.label}
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

      <main className="pt-24">
        {/* Sadece harita kalsın */}

        <section className="relative z-10 w-full">
          <div className="mx-auto w-full px-4 py-12">
            <div className="flex items-center justify-center gap-4 w-full">
              {/* Leaflet Map */}
              <div className="relative z-10 w-full flex justify-center">
                <LeafletTurkeyMap />
              </div>
            </div>
          </div>
        </section>

        {/* Grafikler Bölümü */}
        <section ref={chartsSectionRef} className="py-16">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-2xl font-bold mb-8 text-center">Enerji İstatistikleri</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Bar Chart */}
              <div className="bg-[#a78bfa]/30 rounded-2xl p-4 border border-white/10">
                <h3 className="text-base font-semibold mb-3">Aylık Tüketim</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgb(158, 115, 208)" />
                    <XAxis dataKey="name" stroke="#a78bfa" fontSize={12} />
                    <YAxis stroke="#a78bfa" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#000035', border: '1px solid #a78bfa', borderRadius: '8px', color: '#fff' }} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Bar dataKey="tüketim" fill="#fbbf24" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Line Chart */}
              <div className="bg-[#a78bfa]/30 rounded-2xl p-4 border border-white/10">
                <h3 className="text-base font-semibold mb-3">Toplam Tüketim Enerjisi</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={lineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(199, 151, 255, 0.92)" />
                    <XAxis dataKey="ay" stroke="#a78bfa" fontSize={12} />
                    <YAxis stroke="#a78bfa" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#000035', border: '1px solid #a78bfa', borderRadius: '8px', color: '#fff' }} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Line type="monotone" dataKey="üretim" stroke="#fbbf24" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Pie Chart */}
              <div className="bg-[#a78bfa]/30 rounded-2xl p-4 border border-white/10">
                <h3 className="text-base font-semibold mb-3">Sektör Dağılımı</h3>
                <ResponsiveContainer width="100%" height={220}>
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
                      outerRadius={70}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#000035', border: '1px solid #00FFFF', borderRadius: '8px', color: '#fff' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Area Chart */}
              <div className="bg-[#a78bfa]/30 rounded-2xl p-4 border border-white/10">
                <h3 className="text-base font-semibold mb-3">Günlük Güç Dağılımı</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={areaData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis dataKey="zaman" stroke="#a78bfa" fontSize={12} />
                    <YAxis stroke="#a78bfa" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#000035', border: '1px solid #a78bfa', borderRadius: '8px', color: '#fff' }} />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Area type="monotone" dataKey="güç" stroke="#fbbf24" fill="#fbbf24" fillOpacity={0.3} />
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
