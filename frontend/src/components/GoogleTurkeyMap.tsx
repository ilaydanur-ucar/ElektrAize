import { GoogleMap, useLoadScript } from '@react-google-maps/api'
import { GOOGLE_MAPS_API_KEY } from '../config'

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '520px',
  borderRadius: 12,
}

const center = { lat: 39.0, lng: 35.0 }

export default function GoogleTurkeyMap() {
  const apiKey = GOOGLE_MAPS_API_KEY as string | undefined

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: apiKey || '',
    id: 'elektraize-gmaps',
  })

  if (!apiKey) {
    return <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">Google Maps API anahtarı eksik. Proje kökünde <code>.env</code> dosyasına <code>VITE_GOOGLE_MAPS_API_KEY=YOUR_KEY</code> ekleyin ve yeniden başlatın.</div>
  }
  if (loadError) {
    console.error('Google Maps yükleme hatası:', loadError)
    return (
      <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
        Harita yüklenemedi. Olası nedenler: geçersiz/izinli olmayan API anahtarı, faturalandırma kapalı, veya domain kısıtı.
      </div>
    )
  }
  if (!isLoaded) return <div className="text-sm text-gray-600">Harita yükleniyor...</div>

  return (
    <div className="flex items-center gap-4">
      {/* Sol dış tarafta dikey etiketler */}
      <div className="pointer-events-auto shrink-0">
        <div className="flex flex-col gap-2 rounded-xl border border-gray-200 bg-[#2E3B49] p-3 shadow-sm text-white dark:border-gray-700">
          {['mezken', 'aydınlanma', 'tarım', 'ticaret', 'genel', 'sanayi', 'diğer'].map((label) => (
            <div
              key={label}
              className="select-none rounded-md px-3 py-1 text-sm font-medium text-white/95 hover:bg-[#3065AC]"
            >
              {label}
            </div>
          ))}
        </div>
      </div>

      {/* Harita sağda */}
      <div className="w-[900px] max-w-full rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
        <GoogleMap
          mapContainerStyle={containerStyle}
          center={center}
          zoom={5}
          options={{
            disableDefaultUI: true,
            gestureHandling: 'greedy',
            mapId: undefined,
          }}
        />
      </div>
    </div>
  )
}


