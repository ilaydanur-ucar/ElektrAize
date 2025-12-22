import { useEffect, useRef, useState } from 'react'

// Window interface'ini genişlet
declare global {
  interface Window {
    handleCityClick?: (stateId: string, stateName: string) => void
  }
}

interface TurkeyMapProps {
  onCitySelect?: (city: { id: string, name: string }) => void
  dark: boolean
}

export default function TurkeyMap({ onCitySelect, dark }: TurkeyMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const [selectedCity, setSelectedCity] = useState<{ id: string, name: string } | null>(null)

  // onCitySelect referansını ref olarak tut (dependency loop'u önlemek için)
  const onCitySelectRef = useRef(onCitySelect)

  useEffect(() => {
    onCitySelectRef.current = onCitySelect
  }, [onCitySelect])

  useEffect(() => {
    // Global callback fonksiyonu - harita bu fonksiyonu çağıracak
    window.handleCityClick = (stateId: string, stateName: string) => {
      console.log('🗺️ Şehir tıklandı!')
      console.log('📍 Şehir ID (Plaka):', stateId)
      console.log('🏙️ Şehir Adı:', stateName)

      const cityData = { id: stateId, name: stateName }
      setSelectedCity(cityData)

      // Parent component'e bildir
      if (onCitySelectRef.current) {
        onCitySelectRef.current(cityData)
      }
    }

    const loadScript = (src: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        // Eğer script zaten yüklüyse, kaldır ve yeniden yükle
        const existingScript = document.querySelector(`script[src="${src}"]`)
        if (existingScript) {
          existingScript.remove()
        }

        const script = document.createElement('script')
        script.src = src
        script.type = 'text/javascript'
        script.async = false
        script.onload = () => {
          console.log(`Loaded: ${src}`)
          resolve()
        }
        script.onerror = () => reject(new Error(`Failed to load script: ${src}`))
        document.head.appendChild(script)
      })
    }

    const initMap = async () => {
      try {
        console.log('Harita yükleniyor...')

        // Önce eski map div'ini temizle
        if (mapContainerRef.current) {
          mapContainerRef.current.innerHTML = '<div id="map"></div>'
        }

        // Script'leri yükle
        await loadScript('/html5countrymapv4.5/mapdata.js')

        // Rengi güncelle (Script'ten gelen global değişkeni editle)
        if ((window as any).simplemaps_countrymap_mapdata) {
          (window as any).simplemaps_countrymap_mapdata.main_settings.state_color = dark ? "#3a49b8" : "#f4f5fc";
          // Kenar rengini de ayarlayalım ki light modda harita sınırları belli olsun
          (window as any).simplemaps_countrymap_mapdata.main_settings.border_color = dark ? "transparent" : "#7aa4f5";
          (window as any).simplemaps_countrymap_mapdata.main_settings.border_size = dark ? 0 : 2;
          (window as any).simplemaps_countrymap_mapdata.main_settings.state_hover_color = dark ? "#ffe646" : "#fef08a";
        }

        await loadScript('/html5countrymapv4.5/countrymap.js')

        console.log('Harita başarıyla yüklendi!')
        console.log('✅ Şehirlere tıklayabilirsiniz!')

      } catch (error) {
        console.error('Harita yüklenirken hata:', error)
      }
    }

    // Haritayı her tema değişiminde yeniden başlat
    const timer = setTimeout(() => {
      initMap()
    }, 100)

    return () => {
      clearTimeout(timer)
      if (window.handleCityClick) {
        delete window.handleCityClick
      }
    }
  }, [dark]) // dark değişince çalışır

  // Seçilen şehir değiştiğinde
  useEffect(() => {
    if (selectedCity) {
      console.log('🎯 Aktif şehir:', selectedCity.name, `(${selectedCity.id})`)
    }
  }, [selectedCity])

  return (
    <div className="w-full relative">
      {/* Seçilen şehir bilgisi - Sabit pozisyon, haritanın üstünde */}
      {selectedCity && (
        <div
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="fixed top-24 right-8 z-50 p-4 bg-purple-500/90 backdrop-blur-md border border-purple-400/50 rounded-lg shadow-xl cursor-pointer hover:bg-purple-500 transition-colors"
          title="Haritaya dönmek için tıklayın"
        >
          <p className="text-lg">
            <span className="font-semibold">Seçilen Şehir:</span>{' '}
            <span className="text-white">{selectedCity.name}</span>
            {' '}
            <span className="text-sm text-purple-200">({selectedCity.id})</span>
          </p>
        </div>
      )}

      {/* Harita */}
      <div
        ref={mapContainerRef}
        className="w-full flex justify-center items-center"
        style={{ minHeight: '800px' }}
      >
        <div id="map" style={{ width: '100%', maxWidth: '1600px', height: '800px' }}></div>
      </div>
    </div>
  )
}
