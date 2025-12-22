
import React, { useEffect, useState } from 'react';

// Cloud configuration
const CLOUD_IMAGES = [
    '/cloud.png',
    '/cloud (1).png',
    '/cloud (2).png'
];

interface Cloud {
    id: number;
    src: string;
    top: number; // Percentage
    duration: number; // Seconds
    delay: number; // Seconds
    scale: number;
    opacity: number;
}

const CloudBackground: React.FC = () => {
    const [clouds, setClouds] = useState<Cloud[]>([]);

    useEffect(() => {
        // Generate initial clouds
        const initialClouds: Cloud[] = Array.from({ length: 5 }).map((_, i) => ({
            id: i,
            src: CLOUD_IMAGES[Math.floor(Math.random() * CLOUD_IMAGES.length)],
            top: Math.random() * 80 + 5, // 5% to 85% vertical
            duration: Math.random() * 20 + 30, // 30s to 50s duration (slow)
            delay: Math.random() * -20, // Start mid-animation
            scale: Math.random() * 0.5 + 0.5, // 0.5x to 1x size
            opacity: Math.random() * 0.4 + 0.6 // 0.6 to 1.0 opacity
        }));
        setClouds(initialClouds);
    }, []);

    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
            {clouds.map((cloud) => (
                <img
                    key={cloud.id}
                    src={cloud.src}
                    alt=""
                    className="absolute left-[-20%] animate-float-clouds"
                    style={{
                        top: `${cloud.top}%`,
                        width: `${200 * cloud.scale}px`,
                        opacity: cloud.opacity,
                        animationDuration: `${cloud.duration}s`,
                        animationDelay: `${cloud.delay}s`,
                        animationTimingFunction: 'linear',
                        animationIterationCount: 'infinite'
                    }}
                />
            ))}
        </div>
    );
};

export default CloudBackground;
