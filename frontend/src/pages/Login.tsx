
import { useState, useEffect } from 'react'
import { supabase } from '../supabaseClient'
import { useNavigate } from 'react-router-dom'
import CloudBackground from '../components/CloudBackground'
import StarBackground from '../components/StarBackground'

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [dark, setDark] = useState(false)
    const navigate = useNavigate()

    // Dashboard ile aynı localStorage mantığı
    useEffect(() => {
        const saved = localStorage.getItem('elektraize-theme')
        const isDark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
        setDark(isDark)
    }, [])

    useEffect(() => {
        if (dark) {
            document.documentElement.classList.add('dark')
            localStorage.setItem('elektraize-theme', 'dark')
        } else {
            document.documentElement.classList.remove('dark')
            localStorage.setItem('elektraize-theme', 'light')
        }
    }, [dark])

    // Hata mesajlarını Türkçeye çevir
    const translateError = (errorMessage: string): string => {
        const errorMap: Record<string, string> = {
            "Invalid email": "Geçersiz email formatı",
            "Invalid login credentials": "Email veya şifre hatalı",
            "Email not confirmed": "Email adresinizi doğrulamanız gerekiyor",
            "User already registered": "Bu email adresi zaten kayıtlı",
            "Password should be at least 6 characters": "Şifre en az 6 karakter olmalı",
            "Email rate limit exceeded": "Çok fazla deneme yaptınız. Lütfen daha sonra tekrar deneyin",
            "Failed to fetch": "Bağlantı hatası. İnternet bağlantınızı kontrol edin",
        }

        // Eğer mesaj map'te varsa Türkçe versiyonunu döndür, yoksa orijinal mesajı döndür
        return errorMap[errorMessage] || errorMessage
    }

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        // Email formatı kontrolü
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(email)) {
            setError('Geçersiz email formatı')
            setLoading(false)
            return
        }

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        })

        if (error) {
            setError(translateError(error.message))
            setLoading(false)
        } else {
            navigate('/')
        }
    }

    const handleSignUp = async () => {
        setLoading(true)
        setError(null)
        // Email formatı kontrolü
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(email)) {
            setError('Geçersiz email formatı')
            setLoading(false)
            return
        }
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
        })

        if (error) {
            setError(translateError(error.message))
        } else if (data.user && data.user.identities && data.user.identities.length === 0) {
            // Email zaten kayıtlı
            setError('Bu email adresi zaten kayıtlı')
        } else if (data.session) {
            // Confirm Email kapalıysa direkt giriş yap
            navigate('/')
        } else {
            // Confirm Email açıksa uyarı ver
            setError('Kayıt başarılı! Doğrulama maili gelmediyse spam klasörünüzü kontrol edin.')
        }
        setLoading(false)
    }

    return (
        <div className={`h-screen overflow-hidden flex items-end justify-center pb-0 transition-colors duration-300 ease-in-out ${dark ? 'bg-[#000035]' : 'bg-[#7aa4f5]'}`}>
            {!dark && <CloudBackground />}
            {dark && <StarBackground />}
            {/* Theme Toggle - Absolute Top Left */}
            <button
                onClick={() => setDark((v) => !v)}
                className="absolute top-10 left-10 inline-flex items-center justify-center rounded-full w-36 h-36 bg-transparent hover:bg-black/5 dark:hover:bg-white/10 transition-all duration-200"
                title={dark ? 'Gündüz moduna geç' : 'Gece moduna geç'}
            >
                <img
                    src={dark ? '/crescent-moon.png' : '/contrast.png'}
                    alt={dark ? 'Gece modu' : 'Gündüz modu'}
                    className="w-32 h-32 object-contain filter drop-shadow-md"
                />
            </button>

            <div className={`flex items-end justify-center gap-[290px] scale-90 origin-bottom relative w-fit mx-auto`}>
                {/* Connecting Wire */}
                {/* DO NOT MODIFY: Pole and Wire positions are locked per user request */}
                {/* Left Wire (Back Layer - z-20) - Connects Left Tips of LOWER Bar */}
                <svg className="absolute bottom-0 left-0 w-full h-[700px] overflow-visible pointer-events-none z-20">
                    <path
                        d="M -62 116 Q 492 170 1034 56"
                        fill="none"
                        stroke="#374151"
                        strokeWidth="3"
                        className="drop-shadow-md"
                    />
                    <circle cx="-62" cy="116" r="5" fill="#4b5563" />
                    <circle cx="1034" cy="56" r="5" fill="#4b5563" />
                </svg>

                {/* Right Wire (Front Layer - z-50) - Connects Right Tips of LOWER Bar */}
                <svg className="absolute bottom-0 left-0 w-full h-[700px] overflow-visible pointer-events-none z-50">
                    <path
                        d="M 78 132 Q 620 195 1174 72"
                        fill="none"
                        stroke="#374151"
                        strokeWidth="3"
                        className="drop-shadow-md"
                    />
                    <circle cx="78" cy="132" r="5" fill="#4b5563" />
                    <circle cx="1174" cy="72" r="5" fill="#4b5563" />
                </svg>

                {/* Birds on Wire - Conditional based on theme */}
                {/* Pigeon (Day Mode) - Right side of wire */}
                {!dark && (
                    <img
                        src="/pigeon.png"
                        alt="Pigeon"
                        className="absolute w-24 h-24 object-contain z-50 transition-all duration-500 ease-in-out"
                        style={{
                            left: '814px',
                            bottom: '600px',
                            filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))',
                        }}
                    />
                )}

                {/* Owl (Night Mode) - Left side of wire */}
                {dark && (
                    <img
                        src="/night.png"
                        alt="Owl"
                        className="absolute w-28 h-28 object-contain z-50 transition-all duration-500 ease-in-out"
                        style={{
                            left: '250px',
                            bottom: '550px',
                            filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.5))',
                        }}
                    />
                )}
                {/* Sol Direk - En Üst Katman */}
                <div className={`w-4 h-[640px] rounded-t-lg relative transition-colors duration-300 ease-in-out z-30 ${dark ? 'bg-gray-600' : 'bg-gray-400'}`}>
                    {/* Top Short Bar */}
                    <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-24 h-3 origin-center skew-y-6 ${dark ? 'bg-gray-600' : 'bg-gray-400'}`}></div>
                    {/* Bottom Long Bar */}
                    <div className={`absolute top-16 left-1/2 -translate-x-1/2 w-40 h-4 origin-center skew-y-6 ${dark ? 'bg-gray-600' : 'bg-gray-400'}`}></div>
                </div>

                <div className="w-[500px] h-[600px] flex flex-col justify-center relative overflow-visible transition-all duration-300 ease-in-out mb-[60px] z-40">

                    <div className="relative z-10 text-center mb-8">
                        <div className="flex items-center justify-center gap-4 mt-8 mb-2">
                            <h1 className={`text-6xl font-bold tracking-tight transition-colors duration-500 text-white`}>ElektrAize</h1>
                            <img
                                src="/lightning (4).png"
                                alt="Lightning"
                                className="h-20 w-auto object-contain drop-shadow-[0_0_15px_rgba(250,204,21,0.5)]"
                            />
                        </div>
                        <p className={`text-lg font-medium tracking-wide transition-colors duration-500 text-white/80`}>Enerji Tüketim Analiz Platformu</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-4 relative z-10 px-8 flex flex-col items-center">
                        <div className="w-full">
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className={`w-full border rounded-full px-6 py-4 text-base placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all duration-500 shadow-md ${dark ? 'bg-white/5 border-white/10 text-white' : 'bg-white/10 border-white/20 text-white'}`}
                                placeholder="email"
                            />
                        </div>

                        <div className="w-full">
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className={`w-full border rounded-full px-6 py-4 text-base placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all duration-500 shadow-md ${dark ? 'bg-white/5 border-white/10 text-white' : 'bg-white/10 border-white/20 text-white'}`}
                                placeholder="şifre"
                            />
                        </div>

                        <div className="flex gap-4 w-full justify-center mt-2">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-32 bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-300 hover:to-yellow-400 text-gray-900 font-bold py-3 rounded-full shadow-lg shadow-yellow-600/40 transition-all duration-200 transform hover:scale-[1.05] active:scale-[0.95] disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                            >
                                {loading ? '...' : 'Giriş Yap'}
                            </button>

                            <button
                                type="button"
                                onClick={handleSignUp}
                                disabled={loading}
                                className={`w-32 border font-medium py-3 rounded-full shadow-lg transition-all duration-200 transform hover:scale-[1.05] active:scale-[0.95] disabled:opacity-50 disabled:cursor-not-allowed text-sm ${dark ? 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10' : 'bg-white/50 border-blue-300 text-blue-900 hover:bg-white/80'}`}
                            >
                                Kayıt Ol
                            </button>
                        </div>

                        {/* Error Messages (Only shows if error exists) */}
                        <div className="w-full text-center space-y-2 mt-4 min-h-[24px]">
                            {error && (
                                <div className="text-white text-sm bg-blue-500/20 px-4 py-2 rounded-full inline-block border border-blue-400/30 backdrop-blur-sm">
                                    {error}
                                </div>
                            )}
                        </div>
                    </form>
                </div>

                {/* Sağ Direk - En Alt Katman */}
                <div className={`w-4 h-[700px] rounded-t-lg relative transition-colors duration-300 ease-in-out z-10 ${dark ? 'bg-gray-600' : 'bg-gray-400'}`}>
                    {/* Top Short Bar */}
                    <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-24 h-3 origin-center skew-y-6 ${dark ? 'bg-gray-600' : 'bg-gray-400'}`}></div>
                    {/* Bottom Long Bar */}
                    <div className={`absolute top-16 left-1/2 -translate-x-1/2 w-40 h-4 origin-center skew-y-6 ${dark ? 'bg-gray-600' : 'bg-gray-400'}`}></div>
                </div>
            </div>
        </div>
    )
}
