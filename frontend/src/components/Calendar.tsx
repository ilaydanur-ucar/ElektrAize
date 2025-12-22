import { useState, useMemo } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface CalendarProps {
    startDate?: string
    endDate?: string
    onChange: (start: string, end: string) => void
    onClose: () => void
}

const MIN_DATE = new Date('2022-01-01')
const MAX_DATE = new Date('2025-08-01')

export default function Calendar({ startDate, endDate, onChange, onClose }: CalendarProps) {
    // Görünür ay (seçili tarihten veya bugünden başlar)
    const [currentDate, setCurrentDate] = useState(() => {
        if (startDate) return new Date(startDate)
        return new Date() // Varsayılan bugün
    })

    // Geçici seçimler (Tamam diyene kadar)
    const [tempStart, setTempStart] = useState<string | undefined>(startDate)
    const [tempEnd, setTempEnd] = useState<string | undefined>(endDate)

    // Ayın günlerini oluştur
    const daysInMonth = useMemo(() => {
        const year = currentDate.getFullYear()
        const month = currentDate.getMonth()
        const firstDay = new Date(year, month, 1)
        const lastDay = new Date(year, month + 1, 0)

        // Pazartesi ile başlaması için (0=Pazar ama biz Pzt=0 istiyoruz)
        // getDay(): 0(Sun), 1(Mon)...6(Sat)
        // Bizim düzen: 0(Mon)...6(Sun)
        let startDay = firstDay.getDay() - 1
        if (startDay === -1) startDay = 6

        const days = []

        // Boş kutular (önceki aydan)
        for (let i = 0; i < startDay; i++) {
            days.push(null)
        }

        // Gerçek günler
        for (let i = 1; i <= lastDay.getDate(); i++) {
            days.push(new Date(year, month, i))
        }

        return days
    }, [currentDate])

    const handleDateClick = (date: Date) => {
        const dateStr = date.toISOString().split('T')[0]

        // Eğer hiç seçim yoksa veya iki tarih de seçiliyse -> Yeni başlangıç
        if (!tempStart || (tempStart && tempEnd)) {
            setTempStart(dateStr)
            setTempEnd(undefined)
        }
        // Sadece başlangıç varsa -> Bitiş'i seç (tarih kontrolü yap)
        else if (tempStart && !tempEnd) {
            if (dateStr < tempStart) {
                // Eğer seçilen tarih başlangıçtan önceyse, yer değiştir
                setTempEnd(tempStart)
                setTempStart(dateStr)
            } else {
                setTempEnd(dateStr)
            }
        }
    }

    const handlePrevMonth = () => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1)
        if (newDate >= new Date(MIN_DATE.getFullYear(), MIN_DATE.getMonth(), 1)) {
            setCurrentDate(newDate)
        }
    }

    const handleNextMonth = () => {
        const newDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1)
        if (newDate <= MAX_DATE) {
            setCurrentDate(newDate)
        }
    }

    const isDateDisabled = (date: Date) => {
        return date < MIN_DATE || date > MAX_DATE
    }

    const isSelected = (date: Date) => {
        const str = date.toISOString().split('T')[0]
        return str === tempStart || str === tempEnd
    }

    const isInRange = (date: Date) => {
        if (!tempStart || !tempEnd) return false
        const str = date.toISOString().split('T')[0]
        return str > tempStart && str < tempEnd
    }

    const formatMonth = (date: Date) => {
        return date.toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })
    }

    const applySelection = () => {
        if (tempStart && tempEnd) {
            onChange(tempStart, tempEnd)
            onClose()
        }
    }

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-xl p-4 w-[320px] text-gray-800 animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg capitalize text-gray-900">
                    {formatMonth(currentDate)}
                </h3>
                <div className="flex gap-1">
                    <button
                        onClick={handlePrevMonth}
                        disabled={currentDate <= new Date(MIN_DATE.getFullYear(), MIN_DATE.getMonth(), 1)}
                        className="p-1 hover:bg-gray-100 rounded-full disabled:opacity-30 transition-colors"
                    >
                        {/* Sol Ok SVG */}
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
                    </button>
                    <button
                        onClick={handleNextMonth}
                        disabled={currentDate >= new Date(MAX_DATE.getFullYear(), MAX_DATE.getMonth(), 1)}
                        className="p-1 hover:bg-gray-100 rounded-full disabled:opacity-30 transition-colors"
                    >
                        {/* Sağ Ok SVG */}
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    </button>
                </div>
            </div>

            {/* Days Header */}
            <div className="grid grid-cols-7 mb-2">
                {['Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pa'].map(d => (
                    <div key={d} className="text-center text-xs text-gray-500 font-medium py-1">
                        {d}
                    </div>
                ))}
            </div>

            {/* Grid */}
            <div className="grid grid-cols-7 gap-1 mb-4">
                {daysInMonth.map((date, i) => {
                    if (!date) return <div key={`empty-${i}`} className="h-9" />

                    const disabled = isDateDisabled(date)
                    const selected = isSelected(date)
                    const range = isInRange(date)

                    return (
                        <button
                            key={i}
                            onClick={() => !disabled && handleDateClick(date)}
                            disabled={disabled}
                            className={`
                        h-9 w-full rounded-md flex items-center justify-center text-sm transition-all relative
                        ${disabled ? 'text-gray-300 cursor-not-allowed' : 'hover:bg-blue-50 cursor-pointer'}
                        ${selected ? 'bg-[#007bff] text-white hover:bg-blue-600 font-semibold shadow-sm z-10' : ''}
                        ${range ? 'bg-blue-50 text-blue-700' : ''}
                        ${!selected && !range && !disabled ? 'text-gray-700' : ''}
                    `}
                        >
                            {date.getDate()}
                        </button>
                    )
                })}
            </div>

            {/* Footer / Actions */}
            <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                <button
                    onClick={() => {
                        setTempStart(undefined)
                        setTempEnd(undefined)
                    }}
                    className="text-sm text-blue-500 hover:text-blue-700 font-medium px-2 py-1 rounded"
                >
                    Temizle
                </button>
                <button
                    onClick={applySelection}
                    disabled={!tempStart || !tempEnd}
                    className="text-sm bg-[#007bff] text-white px-4 py-1.5 rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium shadow-sm"
                >
                    Tamam
                </button>
            </div>

            {/* Seçim Bilgisi (Opsiyonel ama kullanışlı) */}
            <div className="text-xs text-center text-gray-400 mt-2 h-4">
                {tempStart && tempEnd ? (
                    `${new Date(tempStart).toLocaleDateString('tr-TR')} - ${new Date(tempEnd).toLocaleDateString('tr-TR')}`
                ) : (
                    tempStart ? 'Bitiş tarihini seçin...' : 'Başlangıç tarihini seçin...'
                )}
            </div>
        </div>
    )
}
