// API Types
export interface AnomalyItem {
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

export interface CategoryInfo {
    loaded: boolean
    train_score?: number
    test_score?: number
    target_column?: string
}

export interface CategoriesResponse {
    available_categories: string[]
    models_loaded: Record<string, boolean>
    details: Record<string, CategoryInfo>
}

// API Configuration
const API_BASE_URL = 'http://localhost:8000'

// API Functions
export async function fetchAnomalies(
    city: string,
    category: string = 'genel',
    startDate?: string,
    endDate?: string,
    tolerancePct: number = 0.10
): Promise<AnomalyItem[]> {
    try {
        const params = new URLSearchParams({
            category,
            tolerance_pct: tolerancePct.toString(),
        })

        if (city) {
            params.append('city', city.toUpperCase())
        }
        if (startDate) {
            params.append('start', startDate)
        }
        if (endDate) {
            params.append('end', endDate)
        }

        const response = await fetch(`${API_BASE_URL}/anomalies?${params}`)

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `API Error: ${response.status}`)
        }

        const data = await response.json()
        return data
    } catch (error) {
        console.error('Anomali verileri çekilirken hata:', error)
        throw error
    }
}

export async function fetchCategories(): Promise<CategoriesResponse> {
    try {
        const response = await fetch(`${API_BASE_URL}/categories`)

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Kategoriler çekilirken hata:', error)
        throw error
    }
}

export async function checkHealth(): Promise<{ status: string; service: string; version: string }> {
    try {
        const response = await fetch(`${API_BASE_URL}/health`)

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Health check hatası:', error)
        throw error
    }
}
export interface RankingResponse {
    city: string
    rank: number
    total_cities: number
    anomaly_count: number
    message?: string
}

export async function fetchCityRanking(
    city: string,
    category: string = 'genel',
    startDate?: string,
    endDate?: string,
    tolerancePct: number = 0.10
): Promise<RankingResponse> {
    try {
        const params = new URLSearchParams({
            category,
            city: city.toUpperCase(),
            tolerance_pct: tolerancePct.toString()
        })

        if (startDate) params.append('start', startDate)
        if (endDate) params.append('end', endDate)

        const response = await fetch(`${API_BASE_URL}/ranking?${params}`)

        if (!response.ok) {
            throw new Error(`Ranking API Error: ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Sıralama verisi çekilirken hata:', error)
        throw error
    }
}
