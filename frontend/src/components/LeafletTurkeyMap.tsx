import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import L from 'leaflet'
import { useEffect, useState } from 'react'

const containerStyle: React.CSSProperties = {
  width: '100%',
  height: '520px',
  borderRadius: 12,
}

const center: [number, number] = [38.68, 35.24]

// Türkiye için yaklaşık sınır kutusu (SW ve NE köşeleri)
const turkeyBounds: L.LatLngBoundsExpression = [
  [35.5, 25.5], // Güneybatı
  [42.5, 45.0], // Kuzeydoğu
]

// Fix default icon paths for Leaflet in bundlers
// @ts-ignore
delete (L.Icon.Default as any).prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

type Props = { dark?: boolean }

export default function LeafletTurkeyMap({ dark }: Props) {
  const [ilGeoJson, setIlGeoJson] = useState<any | null>(null)

  useEffect(() => {
    let mounted = true
    ;(async () => {
      const sources = ['/tr-cities.json', '/turkey-il.json']
      for (const url of sources) {
        try {
          const res = await fetch(url)
          if (!res.ok) continue
          const data = await res.json()
          if (mounted) {
            setIlGeoJson(data)
            break
          }
        } catch {
          // try next
        }
      }
    })()
    return () => {
      mounted = false
    }
  }, [])
  return (
    <div className="w-[900px] max-w-full rounded-xl overflow-hidden border border-gray-200/40 bg-[#0a0f2b]">
      <MapContainer
        center={center}
        zoom={6}
        minZoom={5}
        maxZoom={12}
        scrollWheelZoom={true}
        dragging={true}
        style={containerStyle}
        className="rounded-xl"
        maxBounds={turkeyBounds}
        maxBoundsViscosity={1.0}
        worldCopyJump={false}
        zoomControl={true}
      >
        {/* OSM tabanlı karo: tema durumuna göre değiştir */}
        {dark ? (
          <TileLayer
            attribution="&copy; OpenStreetMap contributors &copy; CARTO"
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
        ) : (
          <TileLayer
            attribution="&copy; OpenStreetMap contributors &copy; CARTO"
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          />
        )}

        {ilGeoJson && (
          <GeoJSON
            data={ilGeoJson as any}
            style={() => ({
              color: dark ? 'rgba(147, 197, 253, 0.35)' : 'rgba(31, 41, 55, 0.35)',
              weight: 0.8,
              fillColor: 'transparent',
              fillOpacity: 0,
            })}
            onEachFeature={(_feature, layer) => {
              layer.on({
                mouseover: (e) => {
                  const target = e.target as L.Path
                  // Belirgin vurgulama stili
                  target.setStyle({
                    color: dark ? '#00FFFF' : '#2563EB',          // canlı mavi / turkuaz
                    weight: 3,                                   // çizgi kalınlığı
                    fillColor: dark ? 'rgba(0, 255, 255, 0.25)' : 'rgba(37, 99, 235, 0.25)',
                    fillOpacity: 0.5,                            // belirgin dolgu
                  })

                  // katmanı öne al
                  if ((target as any).bringToFront) (target as any).bringToFront()

                  // büyüme efekti
                  const el = target.getElement() as SVGElement
                  if (el) {
                    el.style.transition = 'transform 0.2s ease, fill-opacity 0.2s ease'
                    el.style.transform = 'scale(1.05)'
                  }
                },

                mouseout: (e) => {
                  const target = e.target as L.Path
                  target.setStyle({
                    color: dark ? 'rgba(147, 197, 253, 0.35)' : 'rgba(31, 41, 55, 0.35)',
                    weight: 0.8,
                    fillColor: 'transparent',
                    fillOpacity: 0,
                  })

                  // eski haline döndür
                  const el = target.getElement() as SVGElement
                  if (el) el.style.transform = 'scale(1)'
                },
              })
              layer.once('add', () => {
                ;(layer as any).getElement()?.classList.add('leaflet-province')
              })
            }}
          />
        )}
      </MapContainer>
    </div>
  )
}


