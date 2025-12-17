// Basit çözüm: Simplemaps haritasını direkt kendi test sayfasıyla iframe içinde göster
export default function LeafletTurkeyMap() {
  return (
    <div className="flex gap-4 justify-center w-full">
      <iframe
        src="/html5countrymapv4.5/test.html"
        title="Türkiye Haritası"
        className="w-[1500px] max-w-[95vw] rounded-xl mx-auto"
        style={{
          border: 'none',
          minHeight: '750px',
        }}
      />
    </div>
  )
}
