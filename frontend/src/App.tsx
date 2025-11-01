import { useEffect, useMemo, useState } from 'react'
import LeafletTurkeyMap from './components/LeafletTurkeyMap'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Cell, ResponsiveContainer } from 'recharts'

function App() {
  const [dark, setDark] = useState(false)

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

  // Rastgele grafik verileri
  const barData = useMemo(() => [
    { name: 'Ocak', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Şubat', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Mart', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Nisan', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Mayıs', tüketim: Math.floor(Math.random() * 5000) + 2000 },
    { name: 'Haziran', tüketim: Math.floor(Math.random() * 5000) + 2000 },
  ], [])

  const lineData = useMemo(() => [
    { ay: 'Ocak', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Şubat', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Mart', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Nisan', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Mayıs', üretim: Math.floor(Math.random() * 4000) + 3000 },
    { ay: 'Haziran', üretim: Math.floor(Math.random() * 4000) + 3000 },
  ], [])

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
      <header className="sticky top-0 z-10 backdrop-blur border-b border-white/10 bg-transparent">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src="/Ekran görüntüsü 2025-10-31 200345.png" 
              alt="ElektrAize Logo" 
              className="h-10 w-auto object-contain"
            />
            <div>
              <h1 className="text-xl font-semibold tracking-tight">ElektrAize</h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              className="inline-flex items-center gap-2 rounded-md border border-white/20 px-3 py-2 text-sm shadow-sm bg-white/10 hover:bg-white/15 transition"
            >
              <span>Filtrele</span>
            </button>
            <button
              onClick={() => setDark((v) => !v)}
              className="inline-flex items-center gap-2 rounded-md border border-white/20 px-3 py-2 text-sm shadow-sm bg-white/10 hover:bg-white/15 transition"
            >
              <span className="i">{dark ? '☾' : '☀'}</span>
              <span>{dark ? 'Gece modu' : 'Gündüz modu'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Sol sabit menü - Fixed pozisyon için flex dışında */}
      <div className="fixed left-6 top-24 z-50">
        <div className="flex flex-col gap-0 rounded-2xl border border-white/15 bg-[#2E3B49]/95 px-6 py-16 shadow-lg text-white w-72">
          {['mezken', 'aydınlanma', 'tarım', 'ticaret', 'genel', 'sanayi', 'diğer'].map((label) => (
            <div key={label} className="select-none px-5 py-5 text-base font-semibold text-white/95 hover:bg-[#3065AC] cursor-pointer capitalize border-b border-white/10 last:border-b-0">
              • {label}
            </div>
          ))}
        </div>
      </div>

      <main className="ml-[300px]">
        {/* Sadece harita kalsın */}

        <section>
          <div className="mx-auto max-w-6xl px-4 py-10">
            <div className="flex items-start gap-4">
              {/* Leaflet Map */}
              <div>
                <LeafletTurkeyMap dark={dark} />
              </div>
            </div>
          </div>
        </section>

        {/* Grafikler Bölümü */}
        <section className="py-16">
          <div className="mx-auto max-w-6xl px-4">
            <h2 className="text-2xl font-bold mb-8 text-center">Enerji İstatistikleri</h2>
            
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
