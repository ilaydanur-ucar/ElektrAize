export const API_URL =
  (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

export interface Anomaly {
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

/**
 * Backend FastAPI `/anomalies` endpoint'i ile konuşan helper.
 * Varsayılan kategori: "genel"
 */
export async function getAnomalies(
  city: string,
  category: string = 'genel',
): Promise<Anomaly[]> {
  const params = new URLSearchParams()
  params.set('category', category)
  if (city) params.set('city', city)

  const url = `${API_URL}/anomalies?${params.toString()}`

  const res = await fetch(url)

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(
      `API request failed (${res.status} ${res.statusText})${text ? `: ${text}` : ''}`,
    )
  }

  return res.json()
}


