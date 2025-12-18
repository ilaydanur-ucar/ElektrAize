// Türkiye İl Kodları ve İsimleri Mapping
// TR01 -> ADANA formatında

export const CITY_CODE_TO_NAME: Record<string, string> = {
    'TR01': 'ADANA',
    'TR02': 'ADIYAMAN',
    'TR03': 'AFYONKARAHISAR',
    'TR04': 'AGRI',
    'TR05': 'AMASYA',
    'TR06': 'ANKARA',
    'TR07': 'ANTALYA',
    'TR08': 'ARTVIN',
    'TR09': 'AYDIN',
    'TR10': 'BALIKESIR',
    'TR11': 'BILECIK',
    'TR12': 'BINGOL',
    'TR13': 'BITLIS',
    'TR14': 'BOLU',
    'TR15': 'BURDUR',
    'TR16': 'BURSA',
    'TR17': 'CANAKKALE',
    'TR18': 'CANKIRI',
    'TR19': 'CORUM',
    'TR20': 'DENIZLI',
    'TR21': 'DIYARBAKIR',
    'TR22': 'EDIRNE',
    'TR23': 'ELAZIG',
    'TR24': 'ERZINCAN',
    'TR25': 'ERZURUM',
    'TR26': 'ESKISEHIR',
    'TR27': 'GAZIANTEP',
    'TR28': 'GIRESUN',
    'TR29': 'GUMUSHANE',
    'TR30': 'HAKKARI',
    'TR31': 'HATAY',
    'TR32': 'ISPARTA',
    'TR33': 'MERSIN',
    'TR34': 'ISTANBUL',
    'TR35': 'IZMIR',
    'TR36': 'KARS',
    'TR37': 'KASTAMONU',
    'TR38': 'KAYSERI',
    'TR39': 'KIRKLARELI',
    'TR40': 'KIRSEHIR',
    'TR41': 'KOCAELI',
    'TR42': 'KONYA',
    'TR43': 'KUTAHYA',
    'TR44': 'MALATYA',
    'TR45': 'MANISA',
    'TR46': 'KAHRAMANMARAS',
    'TR47': 'MARDIN',
    'TR48': 'MUGLA',
    'TR49': 'MUS',
    'TR50': 'NEVSEHIR',
    'TR51': 'NIGDE',
    'TR52': 'ORDU',
    'TR53': 'RIZE',
    'TR54': 'SAKARYA',
    'TR55': 'SAMSUN',
    'TR56': 'SIIRT',
    'TR57': 'SINOP',
    'TR58': 'SIVAS',
    'TR59': 'TEKIRDAG',
    'TR60': 'TOKAT',
    'TR61': 'TRABZON',
    'TR62': 'TUNCELI',
    'TR63': 'SANLIURFA',
    'TR64': 'USAK',
    'TR65': 'VAN',
    'TR66': 'YOZGAT',
    'TR67': 'ZONGULDAK',
    'TR68': 'AKSARAY',
    'TR69': 'BAYBURT',
    'TR70': 'KARAMAN',
    'TR71': 'KIRIKKALE',
    'TR72': 'BATMAN',
    'TR73': 'SIRNAK',
    'TR74': 'BARTIN',
    'TR75': 'ARDAHAN',
    'TR76': 'IGDIR',
    'TR77': 'YALOVA',
    'TR78': 'KARABUK',
    'TR79': 'KILIS',
    'TR80': 'OSMANIYE',
    'TR81': 'DUZCE',
}

// Ters mapping - ADANA -> TR01
export const CITY_NAME_TO_CODE: Record<string, string> = Object.entries(CITY_CODE_TO_NAME).reduce(
    (acc, [code, name]) => {
        acc[name] = code
        return acc
    },
    {} as Record<string, string>
)

/**
 * Şehir kodundan şehir adını al (Backend için)
 * @param code - TR01, TR02 gibi şehir kodu
 * @returns ADANA, ADIYAMAN gibi büyük harf şehir adı
 */
export function getCityNameFromCode(code: string): string | null {
    return CITY_CODE_TO_NAME[code.toUpperCase()] || null
}

/**
 * Şehir adından şehir kodunu al
 * @param name - ADANA, Adana gibi şehir adı
 * @returns TR01 gibi şehir kodu
 */
export function getCityCodeFromName(name: string): string | null {
    return CITY_NAME_TO_CODE[name.toUpperCase()] || null
}

/**
 * Şehir kodunun geçerli olup olmadığını kontrol et
 */
export function isValidCityCode(code: string): boolean {
    return code.toUpperCase() in CITY_CODE_TO_NAME
}

/**
 * Tüm şehir kodlarını al
 */
export function getAllCityCodes(): string[] {
    return Object.keys(CITY_CODE_TO_NAME)
}

/**
 * Tüm şehir isimlerini al
 */
export function getAllCityNames(): string[] {
    return Object.values(CITY_CODE_TO_NAME)
}
