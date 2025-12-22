
import React, { useEffect, useState } from 'react';

// Star configuration
const STAR_IMAGES = [
    '/star.png',
    '/north-star.png',
    '/christmas-star.png'
];

interface Star {
    id: number;
    src: string;
    top: number; // Percentage
    duration: number; // Seconds
    delay: number; // Seconds
    scale: number;
    opacity: number;
}

const StarBackground: React.FC = () => {
    const [stars, setStars] = useState<Star[]>([]);

    useEffect(() => {
        // Generate initial stars (using same logic/count as clouds for consistency)
        const initialStars: Star[] = Array.from({ length: 5 }).map((_, i) => ({
            id: i,
            src: STAR_IMAGES[Math.floor(Math.random() * STAR_IMAGES.length)],
            top: Math.random() * 80 + 5, // 5% to 85% vertical
            duration: Math.random() * 20 + 30, // 30s to 50s duration (slow float)
            delay: Math.random() * -20, // Start mid-animation
            scale: Math.random() * 0.4 + 0.3, // Slightly smaller than clouds typically
            opacity: Math.random() * 0.5 + 0.5 // 0.5 to 1.0 opacity
        }));
        setStars(initialStars);
    }, []);

    return (
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
            {stars.map((star) => (
                <img
                    key={star.id}
                    src={star.src}
                    alt=""
                    className="absolute left-[-20%] animate-float-clouds" // Reusing the same animation class
                    style={{
                        top: `${star.top}%`,
                        width: `${150 * star.scale}px`, // Base width slightly smaller
                        opacity: star.opacity,
                        animationDuration: `${star.duration}s`,
                        animationDelay: `${star.delay}s`,
                        animationTimingFunction: 'linear', /* Constant speed */
                        animationIterationCount: 'infinite'
                    }}
                />
            ))}
        </div>
    );
};

export default StarBackground;
