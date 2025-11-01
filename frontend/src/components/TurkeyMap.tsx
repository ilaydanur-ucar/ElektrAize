import { useEffect, useMemo, useRef, useState } from 'react'
import { geoMercator, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'

type Topology = {
  type: string
  objects: Record<string, any>
  arcs: any
  transform?: any
}

type ProvinceFeature = GeoJSON.Feature<GeoJSON.Geometry, { name?: string; id?: string }>

type Props = {}

// Veri kaynakları: Sırasıyla dene (yerel -> jsDelivr -> GitHub raw)
const SOURCES: { url: string; kind: 'geojson' | 'topojson' }[] = [
  { url: '/turkey-outline.json', kind: 'geojson' },
]

export default function TurkeyMap({}: Props) {
  const [provinces, setProvinces] = useState<ProvinceFeature[]>([])
  const [hoverName, setHoverName] = useState<string>('')
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [size, setSize] = useState<{ width: number; height: number }>({ width: 800, height: 450 })

  useEffect(() => {
    const handle = () => {
      if (!containerRef.current) return
      const width = containerRef.current.clientWidth
      const height = Math.max(320, Math.round(width * 0.55))
      setSize({ width, height })
    }
    handle()
    window.addEventListener('resize', handle)
    return () => window.removeEventListener('resize', handle)
  }, [])

  useEffect(() => {
    let mounted = true
    ;(async () => {
      for (const src of SOURCES) {
        try {
          const res = await fetch(src.url)
          if (!res.ok) continue
          const data = await res.json()
          if (!mounted) return
          if (src.kind === 'geojson') {
            const fc = data as GeoJSON.FeatureCollection
            setProvinces(fc.features as ProvinceFeature[])
            return
          } else {
            const objKey = Object.keys((data as Topology).objects)[0]
            const fc = feature(data as any, (data as Topology).objects[objKey]) as unknown as GeoJSON.FeatureCollection
            setProvinces(fc.features as ProvinceFeature[])
            return
          }
        } catch {
          // try next source
        }
      }
    })()
    return () => {
      mounted = false
    }
  }, [])

  const projection = useMemo(() => {
    // Sabit merkez ve ölçek: genişliğe göre ölçekle, Türkiye ekranı doldursun
    const baseScale = size.width * 7
    return geoMercator().center([35.2, 39.0]).scale(baseScale).translate([size.width / 2, size.height / 2])
  }, [size.width, size.height])

  const pathGen = useMemo(() => geoPath(projection), [projection])

  return (
    <div ref={containerRef} className="w-full">
      {provinces.length === 0 && (
        <div className="mb-3 text-sm text-gray-600 dark:text-gray-300">Harita yükleniyor...</div>
      )}
      <svg width={size.width} height={size.height} className="rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-800 shadow-soft" aria-label={hoverName || 'Türkiye Haritası'}>
        <g>
          {provinces.map((prov, i) => {
            const name = (prov.properties?.name as string) || (prov.properties?.id as string) || `il-${i}`
            const d = pathGen(prov as any) || undefined
            return (
              <path
                key={name}
                d={d}
                className={`transition fill-gray-100 dark:fill-gray-700 stroke-gray-400 dark:stroke-gray-600`}
                strokeWidth={0.6}
                onMouseEnter={() => setHoverName(name)}
                onMouseLeave={() => setHoverName('')}
                onClick={() => {}}
              />
            )
          })}
        </g>
      </svg>
    </div>
  )
}


