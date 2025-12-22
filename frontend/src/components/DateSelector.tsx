import { useState, useEffect } from 'react'
import { ChevronDown } from 'lucide-react'

interface DateSelectorProps {
    label: string
    value: string
    onChange: (value: string) => void
    dark: boolean
}

export default function DateSelector({ label, value, onChange, dark }: DateSelectorProps) {
    const [day, setDay] = useState('')
    const [month, setMonth] = useState('')
    const [year, setYear] = useState('')

    // Parse initial value
    useEffect(() => {
        if (value) {
            const [y, m, d] = value.split('-')
            setYear(y)
            setMonth(m)
            setDay(d)
        } else {
            setDay('')
            setMonth('')
            setYear('')
        }
    }, [value])

    // Update parent when parts change
    useEffect(() => {
        if (day && month && year) {
            onChange(`${year}-${month}-${day}`)
        }
    }, [day, month, year])

    // Lists
    const years = ['2022', '2023', '2024', '2025']

    const months = [
        { value: '01', label: 'Ocak' },
        { value: '02', label: 'Şubat' },
        { value: '03', label: 'Mart' },
        { value: '04', label: 'Nisan' },
        { value: '05', label: 'Mayıs' },
        { value: '06', label: 'Haziran' },
        { value: '07', label: 'Temmuz' },
        { value: '08', label: 'Ağustos' },
        { value: '09', label: 'Eylül' },
        { value: '10', label: 'Ekim' },
        { value: '11', label: 'Kasım' },
        { value: '12', label: 'Aralık' },
    ]

    // Filter Years based on Month
    const availableYears = years.filter(y => {
        if (y === '2025') {
            // Only allow 2025 if selected month is <= August (08) or no month selected yet
            if (month && parseInt(month) > 8) return false;
        }
        return true;
    })

    // Filter Months based on Year
    const availableMonths = months.filter(m => {
        if (year === '2025') {
            if (parseInt(m.value) > 8) return false;
        }
        return true;
    })

    // Days in month
    const getDaysInMonth = (y: string, m: string) => {
        if (!y || !m) return 31;
        return new Date(parseInt(y), parseInt(m), 0).getDate();
    }

    const maxDays = getDaysInMonth(year || '2024', month || '01')
    const days = Array.from({ length: maxDays }, (_, i) => String(i + 1).padStart(2, '0'))

    // Auto-correct day if month/year changes and day becomes invalid
    useEffect(() => {
        if (!day || !month || !year) return

        const max = getDaysInMonth(year, month)
        if (parseInt(day) > max) {
            setDay(String(max).padStart(2, '0'))
        }
    }, [day, month, year])

    const optionBg = dark ? "bg-[#000035]" : "bg-[#7aa4f5]"

    return (
        <div className="flex flex-col gap-1">
            <label className={`text-sm font-medium ml-1 ${dark ? 'text-gray-300' : 'text-white'}`}>{label}</label>
            <div className="flex gap-2">
                {/* Gün */}
                <div className="relative w-1/4">
                    <select
                        value={day}
                        onChange={(e) => setDay(e.target.value)}
                        className={`w-full appearance-none border rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-cyan-500 text-sm transition-colors ${dark ? 'bg-white/10 border-white/20 text-white' : 'bg-white/20 border-white/30 text-white'}`}
                    >
                        <option value="" className={optionBg}>Gün</option>
                        {days.map(d => (
                            <option key={d} value={d} className={optionBg}>{d}</option>
                        ))}
                    </select>
                    <ChevronDown className={`absolute right-2 top-2.5 w-4 h-4 pointer-events-none ${dark ? 'text-gray-400' : 'text-white/70'}`} />
                </div>

                {/* Ay */}
                <div className="relative w-2/4">
                    <select
                        value={month}
                        onChange={(e) => setMonth(e.target.value)}
                        className={`w-full appearance-none border rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-cyan-500 text-sm transition-colors ${dark ? 'bg-white/10 border-white/20 text-white' : 'bg-white/20 border-white/30 text-white'}`}
                    >
                        <option value="" className={optionBg}>Ay</option>
                        {availableMonths.map(m => (
                            <option key={m.value} value={m.value} className={optionBg}>{m.label}</option>
                        ))}
                    </select>
                    <ChevronDown className={`absolute right-2 top-2.5 w-4 h-4 pointer-events-none ${dark ? 'text-gray-400' : 'text-white/70'}`} />
                </div>

                {/* Yıl */}
                <div className="relative w-1/4">
                    <select
                        value={year}
                        onChange={(e) => setYear(e.target.value)}
                        className={`w-full appearance-none border rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-cyan-500 text-sm transition-colors ${dark ? 'bg-white/10 border-white/20 text-white' : 'bg-white/20 border-white/30 text-white'}`}
                    >
                        <option value="" className={optionBg}>Yıl</option>
                        {availableYears.map(y => (
                            <option key={y} value={y} className={optionBg}>{y}</option>
                        ))}
                    </select>
                    <ChevronDown className={`absolute right-2 top-2.5 w-4 h-4 pointer-events-none ${dark ? 'text-gray-400' : 'text-white/70'}`} />
                </div>
            </div>
        </div>
    )
}
